from .common_imports import *
from .helper import *


# ============================================================
# GET ACTIVE CUSTOMER TENANT
# ============================================================

def get_active_customer_tenant(request):
    user = request.user

    if user.role != "customer":
        return None, Response({
            "success": False,
            "message":
                "Only customer accounts can access this resource."
        }, status=403)

    tenant_slug = (
        request.headers
        .get(
            "X-Tenant-Slug",
            ""
        )
        .strip()
    )

    if not tenant_slug:
        return None, Response({
            "success": False,
            "message":
                "Printing business could not be identified."
        }, status=400)

    tenant = (
        Tenant.objects
        .filter(
            slug=tenant_slug,
            is_active=True
        )
        .first()
    )

    if not tenant:
        return None, Response({
            "success": False,
            "message":
                "Printing business not found."
        }, status=404)

    membership = (
        CustomerTenantMembership.objects
        .filter(
            customer=user,
            tenant=tenant
        )
        .first()
    )

    if not membership:
        return None, Response({
            "success": False,
            "message":
                f"Your account is not connected to {tenant.name}."
        }, status=403)

    if membership.status == "blocked":
        return None, Response({
            "success": False,
            "message":
                f"Your account has been blocked from using {tenant.name}."
        }, status=403)

    if membership.status != "active":
        return None, Response({
            "success": False,
            "message":
                f"Your access to {tenant.name} is currently inactive."
        }, status=403)

    return tenant, None


# ============================================================
# GET DARAJA CONFIGURATION
# ============================================================

def get_daraja_configuration(tenant):
    config = (
        DarajaConfiguration.objects
        .filter(
            tenant=tenant,
            is_active=True
        )
        .first()
    )

    return config


# ============================================================
# GET DARAJA URLS
# ============================================================

def get_daraja_urls(environment):
    if environment == "production":
        return {
            "access_token_url":
                "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials",

            "stk_push_url":
                "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
        }

    return {
        "access_token_url":
            "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials",

        "stk_push_url":
            "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
    }


# ============================================================
# GET ACCESS TOKEN
# ============================================================

def get_access_token(daraja_config):
    try:
        urls = get_daraja_urls(
            daraja_config.environment
        )

        response = requests.get(
            urls["access_token_url"],
            auth=(
                daraja_config.consumer_key,
                daraja_config.consumer_secret,
            ),
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

        access_token = data.get(
            "access_token"
        )

        if not access_token:
            return None

        return access_token

    except requests.RequestException as error:
        print(
            "DARAJA ACCESS TOKEN ERROR:",
            error
        )

        return None

    except Exception as error:
        print(
            "ACCESS TOKEN ERROR:",
            error
        )

        return None


# ============================================================
# NORMALIZE PHONE NUMBER
# ============================================================

def normalize_mpesa_phone(phone_number):
    if not phone_number:
        return None

    phone = (
        str(phone_number)
        .strip()
        .replace(" ", "")
        .replace("-", "")
    )

    if phone.startswith("+254"):
        phone = (
            "254" +
            phone[4:]
        )

    elif phone.startswith("0"):
        phone = (
            "254" +
            phone[1:]
        )

    elif phone.startswith("7"):
        phone = (
            "254" +
            phone
        )

    elif phone.startswith("1"):
        phone = (
            "254" +
            phone
        )

    if not phone.startswith("254"):
        return None

    if len(phone) != 12:
        return None

    if not phone.isdigit():
        return None

    return phone


# ============================================================
# STK PUSH
# ============================================================

def lipa_na_mpesa(
    daraja_config,
    phone_number,
    amount,
    print_job_id
):
    try:
        access_token = (
            get_access_token(
                daraja_config
            )
        )

        if not access_token:
            return {
                "success": False,
                "message":
                    "Failed to get M-Pesa access token."
            }

        phone_number = (
            normalize_mpesa_phone(
                phone_number
            )
        )

        if not phone_number:
            return {
                "success": False,
                "message":
                    "Invalid M-Pesa phone number."
            }

        timestamp = (
            datetime.datetime
            .now()
            .strftime(
                "%Y%m%d%H%M%S"
            )
        )

        shortcode = str(
            daraja_config.short_code
        )

        password_string = (
            f"{shortcode}"
            f"{daraja_config.passkey}"
            f"{timestamp}"
        )

        password = (
            base64.b64encode(
                password_string.encode()
            )
            .decode()
        )

        urls = get_daraja_urls(
            daraja_config.environment
        )

        headers = {
            "Authorization":
                f"Bearer {access_token}",

            "Content-Type":
                "application/json",
        }

        payload = {
            "BusinessShortCode":
                shortcode,

            "Password":
                password,

            "Timestamp":
                timestamp,

            "TransactionType":
                "CustomerPayBillOnline",

            "Amount":
                int(
                    Decimal(amount)
                ),

            "PartyA":
                phone_number,

            "PartyB":
                shortcode,

            "PhoneNumber":
                phone_number,

            "CallBackURL":
                daraja_config.callback_url,

            "AccountReference":
                f"PRINT-{print_job_id}",

            "TransactionDesc":
                "Document Printing Payment",
        }

        response = requests.post(
            urls["stk_push_url"],
            json=payload,
            headers=headers,
            timeout=30,
        )

        try:
            response_data = (
                response.json()
            )

        except ValueError:
            return {
                "success": False,
                "message":
                    "Invalid response from M-Pesa."
            }

        if not response.ok:
            return {
                "success": False,

                "message":
                    response_data.get(
                        "errorMessage"
                    )
                    or response_data.get(
                        "ResponseDescription"
                    )
                    or "M-Pesa request failed.",

                "mpesa":
                    response_data,
            }

        return {
            "success": True,
            "mpesa": response_data,
        }

    except Exception as error:
        print(
            "STK PUSH ERROR:",
            error
        )

        return {
            "success": False,
            "message":
                "Unable to initiate M-Pesa payment."
        }


# ============================================================
# PAY PRINT JOB
# ============================================================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def pay_print_job(request):
    tenant, error_response = (
        get_active_customer_tenant(
            request
        )
    )

    if error_response:
        return error_response

    try:
        print_job_id = (
            request.data.get(
                "print_job_id"
            )
        )

        phone_number = (
            request.data.get(
                "phone_number"
            )
        )

        if not print_job_id:
            return Response({
                "success": False,
                "message":
                    "Print job ID is required."
            }, status=400)

        if not phone_number:
            return Response({
                "success": False,
                "message":
                    "M-Pesa phone number is required."
            }, status=400)

        # ----------------------------------------------------
        # Print job
        # ----------------------------------------------------

        print_job = (
            PrintJob.objects
            .filter(
                id=print_job_id,
                tenant=tenant,
                user=request.user
            )
            .first()
        )

        if not print_job:
            return Response({
                "success": False,
                "message":
                    "Print job not found."
            }, status=404)

        # ----------------------------------------------------
        # Prevent payment on completed/cancelled jobs
        # ----------------------------------------------------

        if print_job.status in [
            "queued",
            "printing",
            "printed",
        ]:
            return Response({
                "success": False,
                "message":
                    "This print job has already been paid for."
            }, status=400)

        if print_job.status == "cancelled":
            return Response({
                "success": False,
                "message":
                    "This print job has been cancelled."
            }, status=400)

        # ----------------------------------------------------
        # Payment
        # ----------------------------------------------------

        payment = (
            Payment.objects
            .filter(
                tenant=tenant,
                user=request.user,
                print_job=print_job
            )
            .first()
        )

        if not payment:
            return Response({
                "success": False,
                "message":
                    "Payment record not found."
            }, status=404)

        if payment.status == "paid":
            return Response({
                "success": False,
                "message":
                    "This print job has already been paid."
            }, status=400)

        # ----------------------------------------------------
        # Daraja configuration
        # ----------------------------------------------------

        daraja_config = (
            get_daraja_configuration(
                tenant
            )
        )

        if not daraja_config:
            return Response({
                "success": False,
                "message":
                    "M-Pesa has not been configured by this printing business."
            }, status=400)

        if not daraja_config.callback_url:
            return Response({
                "success": False,
                "message":
                    "The business M-Pesa callback URL is not configured."
            }, status=400)

        # ----------------------------------------------------
        # Initiate STK push
        # ----------------------------------------------------

        stk_result = (
            lipa_na_mpesa(
                daraja_config=
                    daraja_config,

                phone_number=
                    phone_number,

                amount=
                    payment.amount,

                print_job_id=
                    print_job.id
            )
        )

        if not stk_result.get(
            "success"
        ):
            return Response({
                "success": False,

                "message":
                    stk_result.get(
                        "message",
                        "Unable to initiate payment."
                    ),

                "mpesa":
                    stk_result.get(
                        "mpesa"
                    )

            }, status=400)

        stk_response = (
            stk_result["mpesa"]
        )

        checkout_request_id = (
            stk_response.get(
                "CheckoutRequestID"
            )
        )

        merchant_request_id = (
            stk_response.get(
                "MerchantRequestID"
            )
        )

        if not checkout_request_id:
            return Response({
                "success": False,
                "message":
                    stk_response.get(
                        "ResponseDescription"
                    )
                    or "M-Pesa did not return a checkout request ID."
            }, status=400)

        # ----------------------------------------------------
        # Save request
        # ----------------------------------------------------

        payment.checkout_request_id = (
            checkout_request_id
        )

        payment.status = (
            "pending"
        )

        payment.save(
            update_fields=[
                "checkout_request_id",
                "status",
                "updated_at",
            ]
        )

        return Response({
            "success": True,

            "message":
                "M-Pesa payment request sent. "
                "Check your phone and enter your PIN.",

            "payment": {
                "id":
                    payment.id,

                "amount":
                    payment.amount,

                "status":
                    payment.status,

                "checkout_request_id":
                    payment.checkout_request_id,
            },

            "mpesa": {
                "merchant_request_id":
                    merchant_request_id,

                "checkout_request_id":
                    checkout_request_id,

                "response_code":
                    stk_response.get(
                        "ResponseCode"
                    ),

                "response_description":
                    stk_response.get(
                        "ResponseDescription"
                    ),

                "customer_message":
                    stk_response.get(
                        "CustomerMessage"
                    ),
            }

        })

    except Exception as error:
        print(
            "PAY PRINT JOB ERROR:",
            error
        )

        return Response({
            "success": False,
            "message":
                "Unable to initiate payment."
        }, status=500)


# ============================================================
# M-PESA CALLBACK
# ============================================================

@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def mpesa_callback(request):
    try:
        body = request.data

        stk = (
            body
            .get(
                "Body",
                {}
            )
            .get(
                "stkCallback",
                {}
            )
        )

        result_code = (
            stk.get(
                "ResultCode"
            )
        )

        result_description = (
            stk.get(
                "ResultDesc"
            )
        )

        checkout_request_id = (
            stk.get(
                "CheckoutRequestID"
            )
        )

        merchant_request_id = (
            stk.get(
                "MerchantRequestID"
            )
        )

        if not checkout_request_id:
            return Response({
                "ResultCode": 1,
                "ResultDesc":
                    "CheckoutRequestID missing"
            })

        payment = (
            Payment.objects
            .select_related(
                "print_job",
                "print_job__document",
                "tenant",
                "user",
            )
            .filter(
                checkout_request_id=
                    checkout_request_id
            )
            .first()
        )

        if not payment:
            print(
                "M-PESA CALLBACK PAYMENT NOT FOUND:",
                checkout_request_id
            )

            return Response({
                "ResultCode": 1,
                "ResultDesc":
                    "Payment not found"
            })

        # ----------------------------------------------------
        # Idempotency
        # ----------------------------------------------------

        if payment.status == "paid":
            return Response({
                "ResultCode": 0,
                "ResultDesc":
                    "Already processed"
            })

        # ----------------------------------------------------
        # Successful payment
        # ----------------------------------------------------

        if result_code == 0:
            metadata_items = (
                stk
                .get(
                    "CallbackMetadata",
                    {}
                )
                .get(
                    "Item",
                    []
                )
            )

            metadata = {}

            for item in metadata_items:
                name = item.get(
                    "Name"
                )

                if name:
                    metadata[name] = (
                        item.get(
                            "Value"
                        )
                    )

            payment.status = "paid"

            payment.mpesa_receipt_number = (
                metadata.get(
                    "MpesaReceiptNumber"
                )
            )

            # Daraja normally gives
            # MpesaReceiptNumber, not TransactionID.
            payment.transaction_id = (
                metadata.get(
                    "MpesaReceiptNumber"
                )
            )

            payment.paid_at = (
                timezone.now()
            )

            payment.save(
                update_fields=[
                    "status",
                    "transaction_id",
                    "mpesa_receipt_number",
                    "paid_at",
                    "updated_at",
                ]
            )

            # ------------------------------------------------
            # Queue print job
            # ------------------------------------------------

            print_job = (
                payment.print_job
            )

            print_job.status = (
                "queued"
            )

            print_job.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            # ------------------------------------------------
            # Update document
            # ------------------------------------------------

            document = (
                print_job.document
            )

            document.status = (
                "pending"
            )

            document.save(
                update_fields=[
                    "status"
                ]
            )

            print(
                "M-PESA PAYMENT SUCCESS:",
                {
                    "payment":
                        payment.id,

                    "tenant":
                        payment.tenant_id,

                    "print_job":
                        print_job.id,

                    "receipt":
                        payment.mpesa_receipt_number,
                }
            )

        # ----------------------------------------------------
        # Failed / cancelled STK
        # ----------------------------------------------------

        else:
            payment.status = (
                "failed"
            )

            payment.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            print_job = (
                payment.print_job
            )

            # Keep the print job pending so the
            # customer can retry payment.
            print_job.status = (
                "pending"
            )

            print_job.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            print(
                "M-PESA PAYMENT FAILED:",
                {
                    "payment":
                        payment.id,

                    "result_code":
                        result_code,

                    "result_description":
                        result_description,

                    "merchant_request_id":
                        merchant_request_id,
                }
            )

        return Response({
            "ResultCode": 0,
            "ResultDesc":
                "Accepted"
        })

    except Exception as error:
        print(
            "M-PESA CALLBACK ERROR:",
            error
        )

        return Response({
            "ResultCode": 1,
            "ResultDesc":
                "Server Error"
        })


# ============================================================
# CHECK PRINT JOB STATUS
# ============================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def print_job_status(
    request,
    print_job_id
):
    tenant, error_response = (
        get_active_customer_tenant(
            request
        )
    )

    if error_response:
        return error_response

    try:
        print_job = (
            PrintJob.objects
            .select_related(
                "document",
                "payment",
            )
            .get(
                id=print_job_id,
                tenant=tenant,
                user=request.user
            )
        )

    except PrintJob.DoesNotExist:
        return Response({
            "success": False,
            "message":
                "Print job not found."
        }, status=404)

    payment = getattr(
        print_job,
        "payment",
        None
    )

    return Response({
        "success": True,

        "print_job": {
            "id":
                print_job.id,

            "status":
                print_job.status,

            "copies":
                print_job.copies,

            "paper_size":
                print_job.paper_size,

            "color":
                print_job.color,

            "double_sided":
                print_job.double_sided,

            "created_at":
                print_job.created_at,

            "updated_at":
                print_job.updated_at,
        },

        "document": {
            "id":
                print_job.document.id,

            "name":
                print_job.document.original_name,

            "pages":
                print_job.document.pages,

            "status":
                print_job.document.status,

            "url":
                print_job.document.cloudinary_url,
        },

        "payment": {
            "id":
                payment.id
                if payment
                else None,

            "status":
                payment.status
                if payment
                else "pending",

            "amount":
                str(
                    payment.amount
                )
                if payment
                else "0.00",

            "payment_method":
                payment.payment_method
                if payment
                else None,

            "receipt_number":
                payment.mpesa_receipt_number
                if payment
                else None,

            "checkout_request_id":
                payment.checkout_request_id
                if payment
                else None,

            "paid_at":
                payment.paid_at
                if (
                    payment and
                    payment.status == "paid"
                )
                else None,
        }
    })