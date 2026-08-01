from .common_imports import *
from .helper import *




@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def get_print_job(request):
    if not verify_agent(request):
        return Response({"message": "Unauthorized"}, status=401)

    try:

        job = (
            PrintJob.objects
            .filter(status="queued")
            .select_related("document", "user")
            .order_by("created_at")
            .first()
        )

        if not job:
            return Response({
                "success": False,
                "message": "No pending print jobs."
            })

        document = job.document

        return Response({

            "success": True,

            "print_job": {
                "id": job.id,
                "copies": job.copies,
                "paper_size": job.paper_size,
                "color": job.color,
                "double_sided": job.double_sided,
                "status": job.status,
            },

            "document": {
                "id": document.id,
                "name": document.original_name,
                "pages": document.pages,
                "url": document.cloudinary_url,
                "mime_type": document.mime_type,
            }

        })

    except Exception as e:

        return Response({
            "message": str(e)
        }, status=500)



@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def start_printing(request):
    if not verify_agent(request):
        return Response({"message": "Unauthorized"}, status=401)
    if not verify_agent(request):
        return Response({"message": "Unauthorized"}, status=401)

    try:

        print_job_id = request.data.get("print_job_id")

        job = PrintJob.objects.filter(id=print_job_id).first()

        if not job:
            return Response({
                "message": "Print job not found."
            }, status=404)

        job.status = "printing"
        job.save()

        job.document.status = "printing"
        job.document.save()

        return Response({
            "success": True,
            "message": "Printing started."
        })

    except Exception as e:

        return Response({
            "message": str(e)
        }, status=500)



@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def complete_print_job(request):
    if not verify_agent(request):
        return Response({"message": "Unauthorized"}, status=401)
    if not verify_agent(request):
        return Response({"message": "Unauthorized"}, status=401)

    try:

        print_job_id = request.data.get("print_job_id")

        job = PrintJob.objects.filter(id=print_job_id).first()

        if not job:
            return Response({
                "message": "Print job not found."
            }, status=404)

        job.status = "printed"
        job.save()

        job.document.status = "printed"
        job.document.save()

        return Response({

            "success": True,
            "message": "Document printed successfully."

        })

    except Exception as e:

        return Response({
            "message": str(e)
        }, status=500)



@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def failed_print_job(request):
    if not verify_agent(request):
        return Response({"message": "Unauthorized"}, status=401)
    if not verify_agent(request):
        print("Unauthorized")
        return Response({"message": "Unauthorized"}, status=401)

    try:

        print_job_id = request.data.get("print_job_id")

        reason = request.data.get("reason", "")

        job = PrintJob.objects.filter(id=print_job_id).first()

        if not job:
            return Response({
                "message": "Print job not found."
            }, status=404)

        job.status = "failed"
        job.save()

        return Response({

            "success": True,
            "message": "Print job marked as failed.",
            "reason": reason

        })

    except Exception as e:

        return Response({
            "message": str(e)
        }, status=500)


@api_view(["GET"])
@permission_classes([AllowAny])
def printer_status(request):

    queued = PrintJob.objects.filter(status="queued").count()
    printing = PrintJob.objects.filter(status="printing").count()
    printed = PrintJob.objects.filter(status="printed").count()
    failed = PrintJob.objects.filter(status="failed").count()

    return Response({

        "queued": queued,
        "printing": printing,
        "printed": printed,
        "failed": failed

    })


# for users
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def print_history(request):
    try:
        jobs = (
            PrintJob.objects
            .filter(
                user=request.user,
                # status="printed",
            )
            .select_related(
                "document",
                "payment",
            )
            .order_by("-updated_at")
        )

        history = []

        for job in jobs:
            try:
                payment = job.payment
            except Payment.DoesNotExist:
                payment = None

            history.append({
                "id": job.id,
                "order_number": f"PF-{job.id:04d}",
                "document": {
                    "id": job.document.id,
                    "name": job.document.original_name,
                    "pages": job.document.pages,
                    "url": job.document.cloudinary_url,
                    "size": job.document.size,
                    "mime_type": job.document.mime_type,
                },
                "copies": job.copies,
                "paper_size": job.paper_size,
                "color": job.color,
                "double_sided": job.double_sided,
                "status": job.status,
                "created_at": job.created_at,
                "completed_at": job.updated_at,
                "payment": {
                    "id": payment.id if payment else None,
                    "amount": str(payment.amount) if payment else "0.00",
                    "status": payment.status if payment else "not_found",
                    "payment_method": (
                        payment.payment_method
                        if payment
                        else None
                    ),
                    "mpesa_receipt_number": (
                        payment.mpesa_receipt_number
                        if payment
                        else None
                    ),
                    "paid_at": (
                        payment.paid_at
                        if payment
                        else None
                    ),
                },
            })

        return Response({
            "success": True,
            "count": len(history),
            "history": history,
        })

    except Exception as error:
        return Response({
            "success": False,
            "message": str(error),
        }, status=500)



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_print_receipt(request, print_job_id):
    try:
        print_job = (
            PrintJob.objects
            .select_related(
                "document",
                "payment",
                "user",
            )
            .filter(
                id=print_job_id,
                user=request.user,
            )
            .first()
        )

        if not print_job:
            return Response({
                "success": False,
                "message": "Print job not found.",
            }, status=404)

        try:
            payment = print_job.payment
        except Payment.DoesNotExist:
            return Response({
                "success": False,
                "message": "Payment information not found.",
            }, status=404)

        if payment.status != "paid":
            return Response({
                "success": False,
                "message": "A receipt is only available for paid jobs.",
            }, status=400)

        buffer = BytesIO()

        pdf = canvas.Canvas(
            buffer,
            pagesize=A4,
        )

        width, height = A4

        pdf.setTitle(
            f"PrintFlow Receipt PF-{print_job.id:04d}"
        )

        pdf.setFont("Helvetica-Bold", 20)
        pdf.drawString(
            50,
            height - 60,
            "PrintFlow",
        )

        pdf.setFont("Helvetica", 11)
        pdf.drawString(
            50,
            height - 80,
            "Document Printing Receipt",
        )

        pdf.line(
            50,
            height - 95,
            width - 50,
            height - 95,
        )

        y = height - 130

        receipt_rows = [
            (
                "Order Number",
                f"PF-{print_job.id:04d}",
            ),
            (
                "Document",
                print_job.document.original_name,
            ),
            (
                "Pages",
                str(print_job.document.pages),
            ),
            (
                "Copies",
                str(print_job.copies),
            ),
            (
                "Paper Size",
                print_job.paper_size,
            ),
            (
                "Print Type",
                (
                    "Color"
                    if print_job.color
                    else "Black & White"
                ),
            ),
            (
                "Printing Sides",
                (
                    "Double-Sided"
                    if print_job.double_sided
                    else "Single-Sided"
                ),
            ),
            (
                "Payment Method",
                payment.get_payment_method_display(),
            ),
            (
                "Payment Status",
                payment.status.title(),
            ),
            (
                "M-Pesa Receipt",
                payment.mpesa_receipt_number or "N/A",
            ),
            (
                "Amount Paid",
                f"KES {payment.amount}",
            ),
            (
                "Paid At",
                (
                    payment.paid_at.strftime(
                        "%d %b %Y, %I:%M %p"
                    )
                    if payment.paid_at
                    else "N/A"
                ),
            ),
        ]

        for label, value in receipt_rows:
            pdf.setFont("Helvetica-Bold", 10)
            pdf.drawString(50, y, label)

            pdf.setFont("Helvetica", 10)
            pdf.drawString(190, y, str(value))

            y -= 24

        pdf.line(
            50,
            y - 5,
            width - 50,
            y - 5,
        )

        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(
            50,
            y - 35,
            f"Total: KES {payment.amount}",
        )

        pdf.setFont("Helvetica", 9)
        pdf.drawString(
            50,
            60,
            "Thank you for using PrintFlow.",
        )

        pdf.drawString(
            50,
            45,
            "This receipt was generated electronically.",
        )

        pdf.showPage()
        pdf.save()

        buffer.seek(0)

        filename = (
            f"printflow-receipt-PF-{print_job.id:04d}.pdf"
        )

        return FileResponse(
            buffer,
            as_attachment=True,
            filename=filename,
            content_type="application/pdf",
        )

    except Exception as error:
        return Response({
            "success": False,
            "message": str(error),
        }, status=500)

