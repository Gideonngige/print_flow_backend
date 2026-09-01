from .common_imports import *
from .helper import *


# ============================================================
# HELPER: GET ACTIVE CUSTOMER TENANT
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
# HELPER: GET AGENT TENANT
# ============================================================

def get_agent_tenant(request):
    """
    For now the agent sends:

    X-Tenant-Slug: gtech-company
    X-Agent-Key: <agent-secret>

    verify_agent(request) should still validate
    the agent key.
    """

    if not verify_agent(request):
        return None, Response({
            "success": False,
            "message":
                "Unauthorized print agent."
        }, status=401)

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
                "Print agent tenant was not provided."
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

    return tenant, None


# ============================================================
# AGENT: GET NEXT PRINT JOB
# ============================================================

@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def get_print_job(request):

    tenant, error_response = (
        get_agent_tenant(
            request
        )
    )

    if error_response:
        return error_response

    try:
        job = (
            PrintJob.objects
            .filter(
                tenant=tenant,
                status="queued"
            )
            .select_related(
                "document",
                "user",
                "tenant",
            )
            .order_by(
                "created_at"
            )
            .first()
        )

        if not job:
            return Response({
                "success": False,
                "message":
                    "No queued print jobs."
            })

        document = (
            job.document
        )

        return Response({
            "success": True,

            "tenant": {
                "id":
                    tenant.id,

                "name":
                    tenant.name,

                "slug":
                    tenant.slug,
            },

            "print_job": {
                "id":
                    job.id,

                "copies":
                    job.copies,

                "paper_size":
                    job.paper_size,

                "color":
                    job.color,

                "double_sided":
                    job.double_sided,

                "status":
                    job.status,

                "created_at":
                    job.created_at,
            },

            "customer": {
                "id":
                    job.user.id,

                "full_name":
                    job.user.full_name,

                "email":
                    job.user.email,

                "phone_number":
                    job.user.phone_number,
            },

            "document": {
                "id":
                    document.id,

                "name":
                    document.original_name,

                "pages":
                    document.pages,

                "url":
                    document.cloudinary_url,

                "mime_type":
                    document.mime_type,

                "size":
                    document.size,
            }
        })

    except Exception as error:
        print(
            "GET PRINT JOB ERROR:",
            error
        )

        return Response({
            "success": False,
            "message":
                "Unable to retrieve print job."
        }, status=500)


# ============================================================
# AGENT: START PRINTING
# ============================================================

@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def start_printing(request):

    tenant, error_response = (
        get_agent_tenant(
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

        if not print_job_id:
            return Response({
                "success": False,
                "message":
                    "Print job ID is required."
            }, status=400)

        job = (
            PrintJob.objects
            .filter(
                id=print_job_id,
                tenant=tenant
            )
            .first()
        )

        if not job:
            return Response({
                "success": False,
                "message":
                    "Print job not found."
            }, status=404)

        if job.status != "queued":
            return Response({
                "success": False,
                "message":
                    f"Print job cannot be started while status is {job.status}."
            }, status=400)

        job.status = (
            "printing"
        )

        job.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        document = (
            job.document
        )

        document.status = (
            "printing"
        )

        document.save(
            update_fields=[
                "status"
            ]
        )

        return Response({
            "success": True,
            "message":
                "Printing started.",

            "print_job": {
                "id":
                    job.id,

                "status":
                    job.status,
            }
        })

    except Exception as error:
        print(
            "START PRINTING ERROR:",
            error
        )

        return Response({
            "success": False,
            "message":
                "Unable to start printing."
        }, status=500)


# ============================================================
# AGENT: COMPLETE PRINT JOB
# ============================================================

@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def complete_print_job(request):

    tenant, error_response = (
        get_agent_tenant(
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

        if not print_job_id:
            return Response({
                "success": False,
                "message":
                    "Print job ID is required."
            }, status=400)

        job = (
            PrintJob.objects
            .filter(
                id=print_job_id,
                tenant=tenant
            )
            .first()
        )

        if not job:
            return Response({
                "success": False,
                "message":
                    "Print job not found."
            }, status=404)

        if job.status not in [
            "queued",
            "printing",
        ]:
            return Response({
                "success": False,
                "message":
                    f"Print job cannot be completed while status is {job.status}."
            }, status=400)

        job.status = (
            "printed"
        )

        job.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        document = (
            job.document
        )

        document.status = (
            "printed"
        )

        document.save(
            update_fields=[
                "status"
            ]
        )

        return Response({
            "success": True,

            "message":
                "Document printed successfully.",

            "print_job": {
                "id":
                    job.id,

                "status":
                    job.status,
            }
        })

    except Exception as error:
        print(
            "COMPLETE PRINT JOB ERROR:",
            error
        )

        return Response({
            "success": False,
            "message":
                "Unable to complete print job."
        }, status=500)


# ============================================================
# AGENT: FAILED PRINT JOB
# ============================================================

@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def failed_print_job(request):

    tenant, error_response = (
        get_agent_tenant(
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

        reason = (
            request.data.get(
                "reason",
                ""
            )
            .strip()
        )

        if not print_job_id:
            return Response({
                "success": False,
                "message":
                    "Print job ID is required."
            }, status=400)

        job = (
            PrintJob.objects
            .filter(
                id=print_job_id,
                tenant=tenant
            )
            .first()
        )

        if not job:
            return Response({
                "success": False,
                "message":
                    "Print job not found."
            }, status=404)

        job.status = (
            "failed"
        )

        job.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        document = (
            job.document
        )

        document.status = (
            "failed"
        )

        document.save(
            update_fields=[
                "status"
            ]
        )

        return Response({
            "success": True,

            "message":
                "Print job marked as failed.",

            "reason":
                reason,

            "print_job": {
                "id":
                    job.id,

                "status":
                    job.status,
            }
        })

    except Exception as error:
        print(
            "FAILED PRINT JOB ERROR:",
            error
        )

        return Response({
            "success": False,
            "message":
                "Unable to update print job."
        }, status=500)


# ============================================================
# AGENT: PRINTER / QUEUE STATUS
# ============================================================

@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def printer_status(request):

    tenant, error_response = (
        get_agent_tenant(
            request
        )
    )

    if error_response:
        return error_response

    queued = (
        PrintJob.objects
        .filter(
            tenant=tenant,
            status="queued"
        )
        .count()
    )

    printing = (
        PrintJob.objects
        .filter(
            tenant=tenant,
            status="printing"
        )
        .count()
    )

    printed = (
        PrintJob.objects
        .filter(
            tenant=tenant,
            status="printed"
        )
        .count()
    )

    failed = (
        PrintJob.objects
        .filter(
            tenant=tenant,
            status="failed"
        )
        .count()
    )

    return Response({
        "success": True,

        "tenant": {
            "id":
                tenant.id,

            "name":
                tenant.name,

            "slug":
                tenant.slug,
        },

        "queued":
            queued,

        "printing":
            printing,

        "printed":
            printed,

        "failed":
            failed,
    })


# ============================================================
# CUSTOMER: PRINT HISTORY
# ============================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def print_history(request):

    tenant, error_response = (
        get_active_customer_tenant(
            request
        )
    )

    if error_response:
        return error_response

    try:
        jobs = (
            PrintJob.objects
            .filter(
                tenant=tenant,
                user=request.user,
            )
            .select_related(
                "document",
                "payment",
                "tenant",
            )
            .order_by(
                "-updated_at"
            )
        )

        history = []

        for job in jobs:

            payment = getattr(
                job,
                "payment",
                None
            )

            history.append({
                "id":
                    job.id,

                "order_number":
                    f"PF-{job.id:04d}",

                "document": {
                    "id":
                        job.document.id,

                    "name":
                        job.document.original_name,

                    "pages":
                        job.document.pages,

                    "url":
                        job.document.cloudinary_url,

                    "size":
                        job.document.size,

                    "mime_type":
                        job.document.mime_type,
                },

                "copies":
                    job.copies,

                "paper_size":
                    job.paper_size,

                "color":
                    job.color,

                "double_sided":
                    job.double_sided,

                "status":
                    job.status,

                "created_at":
                    job.created_at,

                "updated_at":
                    job.updated_at,

                "payment": {
                    "id":
                        payment.id
                        if payment
                        else None,

                    "amount":
                        str(
                            payment.amount
                        )
                        if payment
                        else "0.00",

                    "status":
                        payment.status
                        if payment
                        else "not_found",

                    "payment_method":
                        payment.payment_method
                        if payment
                        else None,

                    "mpesa_receipt_number":
                        payment.mpesa_receipt_number
                        if payment
                        else None,

                    "paid_at":
                        payment.paid_at
                        if payment
                        else None,
                },
            })

        return Response({
            "success": True,

            "business": {
                "id":
                    tenant.id,

                "name":
                    tenant.name,

                "slug":
                    tenant.slug,
            },

            "count":
                len(history),

            "history":
                history,
        })

    except Exception as error:
        print(
            "PRINT HISTORY ERROR:",
            error
        )

        return Response({
            "success": False,
            "message":
                "Unable to load print history."
        }, status=500)


# ============================================================
# CUSTOMER: DOWNLOAD PRINT RECEIPT
# ============================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_print_receipt(
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
                "user",
                "tenant",
            )
            .filter(
                id=print_job_id,
                tenant=tenant,
                user=request.user,
            )
            .first()
        )

        if not print_job:
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

        if not payment:
            return Response({
                "success": False,
                "message":
                    "Payment information not found."
            }, status=404)

        if payment.status != "paid":
            return Response({
                "success": False,
                "message":
                    "A receipt is only available for paid jobs."
            }, status=400)

        buffer = BytesIO()

        pdf = canvas.Canvas(
            buffer,
            pagesize=A4
        )

        width, height = (
            A4
        )

        order_number = (
            f"PF-{print_job.id:04d}"
        )

        pdf.setTitle(
            f"{tenant.name} Receipt {order_number}"
        )

        # ----------------------------------------------------
        # Business heading
        # ----------------------------------------------------

        pdf.setFont(
            "Helvetica-Bold",
            20
        )

        pdf.drawString(
            50,
            height - 60,
            tenant.name
        )

        pdf.setFont(
            "Helvetica",
            10
        )

        pdf.drawString(
            50,
            height - 78,
            "Document Printing Receipt"
        )

        if tenant.phone_number:
            pdf.drawString(
                50,
                height - 94,
                f"Phone: {tenant.phone_number}"
            )

        if tenant.email:
            pdf.drawString(
                50,
                height - 108,
                f"Email: {tenant.email}"
            )

        pdf.line(
            50,
            height - 125,
            width - 50,
            height - 125,
        )

        y = (
            height - 155
        )

        receipt_rows = [
            (
                "Order Number",
                order_number,
            ),
            (
                "Customer",
                request.user.full_name,
            ),
            (
                "Document",
                print_job.document.original_name,
            ),
            (
                "Pages",
                str(
                    print_job.document.pages
                ),
            ),
            (
                "Copies",
                str(
                    print_job.copies
                ),
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
                (
                    payment.mpesa_receipt_number
                    or "N/A"
                ),
            ),
            (
                "Amount Paid",
                f"KES {payment.amount}",
            ),
            (
                "Paid At",
                (
                    timezone.localtime(
                        payment.paid_at
                    ).strftime(
                        "%d %b %Y, %I:%M %p"
                    )
                    if payment.paid_at
                    else "N/A"
                ),
            ),
        ]

        for label, value in receipt_rows:

            pdf.setFont(
                "Helvetica-Bold",
                10
            )

            pdf.drawString(
                50,
                y,
                label
            )

            pdf.setFont(
                "Helvetica",
                10
            )

            # Truncate very long values
            display_value = str(
                value
            )

            if len(display_value) > 55:
                display_value = (
                    display_value[:52]
                    + "..."
                )

            pdf.drawString(
                190,
                y,
                display_value
            )

            y -= 24

        pdf.line(
            50,
            y - 5,
            width - 50,
            y - 5,
        )

        pdf.setFont(
            "Helvetica-Bold",
            14
        )

        pdf.drawString(
            50,
            y - 35,
            f"Total: KES {payment.amount}"
        )

        pdf.setFont(
            "Helvetica",
            9
        )

        pdf.drawString(
            50,
            60,
            f"Thank you for printing with {tenant.name}."
        )

        pdf.drawString(
            50,
            45,
            "Powered by PrintFlow."
        )

        pdf.drawString(
            50,
            30,
            "This receipt was generated electronically."
        )

        pdf.showPage()
        pdf.save()

        buffer.seek(0)

        filename = (
            f"{tenant.slug}-receipt-"
            f"{order_number}.pdf"
        )

        return FileResponse(
            buffer,
            as_attachment=True,
            filename=filename,
            content_type="application/pdf",
        )

    except Exception as error:
        print(
            "DOWNLOAD RECEIPT ERROR:",
            error
        )

        return Response({
            "success": False,
            "message":
                "Unable to generate receipt."
        }, status=500)