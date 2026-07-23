from .common_imports import *
from .helper import *




# =========================================
# GET ACCESS TOKEN
# =========================================

def get_access_token():
    try:
        response = requests.get(
            os.environ.get("ACCESS_TOKEN_URL"),
            auth=(os.environ.get("MPESA_CONSUMER_KEY"), os.environ.get("MPESA_CONSUMER_SECRET"))
        )

        data = response.json()

        return data.get("access_token")

    except Exception as e:
        print("ACCESS TOKEN ERROR:", e)
        return None


# =========================================
# STK PUSH FUNCTION
# CUSTOMER PAYS FOR EVENT
# =========================================
def lipa_na_mpesa(phone_number, amount, print_job_id):

    amount = int(amount)

    access_token = get_access_token()

    if not access_token:
        return {
            "success": False,
            "message": "Failed to get access token"
        }

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    password = base64.b64encode(
        f"{os.environ.get('MPESA_SHORTCODE')}{os.environ.get('MPESA_PASSKEY')}{timestamp}".encode()
    ).decode()

    phone_number = normalize_phone(phone_number)

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    payload = {
        "BusinessShortCode": os.environ.get("MPESA_SHORTCODE"),
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": os.environ.get("MPESA_SHORTCODE"),
        "PhoneNumber": phone_number,
        "CallBackURL": os.environ.get("MPESA_CALLBACK_URL"),

        "AccountReference": f"PRINT-{print_job_id}",
        "TransactionDesc": "Document Printing Payment"
    }

    response = requests.post(
        os.environ.get("STK_PUSH_URL"),
        json=payload,
        headers=headers
    )

    return response.json()


# pay print job
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def pay_print_job(request):

    try:

        print_job_id = request.data.get("print_job_id")
        phone_number = request.data.get("phone_number")

        print_job = PrintJob.objects.filter(
            id=print_job_id,
            user=request.user
        ).first()

        if not print_job:
            return Response({
                "success": False,
                "message": "Print Job not found."
            }, status=404)

        payment = Payment.objects.filter(
            print_job=print_job
        ).first()

        if not payment:
            return Response({
                "success": False,
                "message": "Payment not found."
            }, status=404)

        stk_response = lipa_na_mpesa(
            phone_number=phone_number,
            amount=payment.amount,
            print_job_id=print_job.id
        )

        checkout_request_id = stk_response.get(
            "CheckoutRequestID"
        )

        payment.checkout_request_id = checkout_request_id
        payment.status = "pending"
        payment.save()

        return Response({

            "success": True,
            "message": "STK Push sent successfully.",

            "payment": {
                "id": payment.id,
                "amount": payment.amount,
                "status": payment.status,
                "checkout_request_id": checkout_request_id
            },

            "mpesa": stk_response

        })

    except Exception as e:

        return Response({
            "success": False,
            "message": str(e)
        }, status=500)




# mpesa callback
@csrf_exempt
@api_view(["POST"])
def mpesa_callback(request):

    try:

        body = json.loads(request.body)

        stk = body.get(
            "Body",
            {}
        ).get(
            "stkCallback",
            {}
        )

        result_code = stk.get("ResultCode")

        checkout_request_id = stk.get(
            "CheckoutRequestID"
        )

        payment = Payment.objects.filter(
            checkout_request_id=checkout_request_id
        ).first()

        if not payment:

            return JsonResponse({
                "ResultCode": 1,
                "ResultDesc": "Payment not found"
            })

        if result_code == 0:

            metadata = stk.get(
                "CallbackMetadata",
                {}
            ).get("Item", [])

            meta = {
                item["Name"]: item.get("Value")
                for item in metadata
            }

            payment.status = "paid"
            payment.transaction_id = meta.get("TransactionID")
            payment.mpesa_receipt_number = meta.get("MpesaReceiptNumber")
            payment.paid_at = timezone.now()

            payment.save()

            # Queue for printing

            print_job = payment.print_job

            print_job.status = "queued"

            print_job.save()

            document = print_job.document

            document.status = "pending"

            document.save()

        else:

            payment.status = "failed"
            payment.save()

            payment.print_job.status = "failed"
            payment.print_job.save()

        return JsonResponse({
            "ResultCode": 0,
            "ResultDesc": "Accepted"
        })

    except Exception as e:

        print(e)

        return JsonResponse({
            "ResultCode": 1,
            "ResultDesc": "Server Error"
        })





# check print job status
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def print_job_status(request, print_job_id):

    try:
        print_job = PrintJob.objects.select_related(
            "document",
            "payment"
        ).get(
            id=print_job_id,
            user=request.user
        )

    except PrintJob.DoesNotExist:
        return Response(
            {
                "message": "Print job not found"
            },
            status=404
        )

    payment = Payment.objects.filter(
        print_job=print_job
    ).first()

    return Response({

        "success": True,

        "print_job": {
            "id": print_job.id,
            "status": print_job.status,
            "copies": print_job.copies,
            "paper_size": print_job.paper_size,
            "color": print_job.color,
            "double_sided": print_job.double_sided,
            "created_at": print_job.created_at,
        },

        "document": {
            "id": print_job.document.id,
            "name": print_job.document.original_name,
            "pages": print_job.document.pages,
            "status": print_job.document.status,
        },

        "payment": {
            "status": payment.status if payment else "pending",
            "amount": str(payment.amount) if payment else "0",
            "receipt_number": (
                payment.mpesa_receipt_number
                if payment
                else None
            ),
            "paid_at": (
                payment.paid_at
                if payment and payment.status == "paid"
                else None
            ),
        }

    })