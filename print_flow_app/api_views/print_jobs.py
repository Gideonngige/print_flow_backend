from .common_imports import *


# ============================================================
# BUSINESS PRINT JOBS
# ============================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def business_print_jobs(request):

    user = request.user

    if user.role not in [
        "business_admin",
        "staff",
    ]:
        return Response({
            "message":
                "You are not allowed to access print jobs."
        }, status=403)

    tenant = user.tenant

    if not tenant:
        return Response({
            "message":
                "Your account is not linked to a business."
        }, status=400)


    # --------------------------------------------------------
    # Query parameters
    # --------------------------------------------------------

    search = (
        request.GET.get(
            "search",
            ""
        )
        .strip()
    )

    status_filter = (
        request.GET.get(
            "status",
            ""
        )
        .strip()
    )


    jobs = (
        PrintJob.objects
        .filter(
            tenant=tenant
        )
        .select_related(
            "user",
            "document",
            "printer",
        )
        .order_by(
            "-created_at"
        )
    )


    # --------------------------------------------------------
    # Search
    # --------------------------------------------------------

    if search:

        jobs = jobs.filter(
            Q(
                document__original_name__icontains=
                    search
            )
            |
            Q(
                user__full_name__icontains=
                    search
            )
            |
            Q(
                user__email__icontains=
                    search
            )
            |
            Q(
                user__phone_number__icontains=
                    search
            )
        )


    # --------------------------------------------------------
    # Status filter
    # --------------------------------------------------------

    valid_statuses = [
        "pending",
        "paid",
        "queued",
        "printing",
        "printed",
        "failed",
        "cancelled",
    ]

    if (
        status_filter and
        status_filter in valid_statuses
    ):
        jobs = jobs.filter(
            status=status_filter
        )


    jobs_data = []

    for job in jobs:

        payment = getattr(
            job,
            "payment",
            None
        )

        printer = getattr(
            job,
            "printer",
            None
        )

        jobs_data.append({
            "id": job.id,

            "customer": {
                "id": job.user.id,
                "name": job.user.full_name,
                "email": job.user.email,
                "phone_number":
                    job.user.phone_number,
            },

            "document": {
                "id":
                    job.document.id,

                "name":
                    job.document.original_name,

                "pages":
                    job.document.pages,

                "mime_type":
                    job.document.mime_type,

                "url":
                    job.document.cloudinary_url,
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

            "printer":
                {
                    "id":
                        printer.id,

                    "name":
                        printer.name,

                    "system_name":
                        printer.system_name,

                    "status":
                        printer.status,
                }
                if printer
                else None,

            "payment":
                {
                    "id":
                        payment.id,

                    "amount":
                        payment.amount,

                    "status":
                        payment.status,

                    "payment_method":
                        payment.payment_method,

                    "mpesa_receipt_number":
                        payment.mpesa_receipt_number,
                }
                if payment
                else None,

            "created_at":
                job.created_at,

            "updated_at":
                job.updated_at,
        })


    # --------------------------------------------------------
    # Counts
    # --------------------------------------------------------

    base_jobs = PrintJob.objects.filter(
        tenant=tenant
    )


    stats = {
        "total":
            base_jobs.count(),

        "pending":
            base_jobs.filter(
                status="pending"
            ).count(),

        "paid":
            base_jobs.filter(
                status="paid"
            ).count(),

        "queued":
            base_jobs.filter(
                status="queued"
            ).count(),

        "printing":
            base_jobs.filter(
                status="printing"
            ).count(),

        "printed":
            base_jobs.filter(
                status="printed"
            ).count(),

        "failed":
            base_jobs.filter(
                status="failed"
            ).count(),

        "cancelled":
            base_jobs.filter(
                status="cancelled"
            ).count(),
    }


    return Response({
        "success": True,
        "count": len(jobs_data),
        "stats": stats,
        "print_jobs": jobs_data,
    })


# ============================================================
# PRINT JOB DETAIL
# ============================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def business_print_job_detail(
    request,
    job_id
):

    user = request.user

    if user.role not in [
        "business_admin",
        "staff",
    ]:
        return Response({
            "message":
                "You are not allowed to access this print job."
        }, status=403)

    tenant = user.tenant

    job = (
        PrintJob.objects
        .filter(
            id=job_id,
            tenant=tenant
        )
        .select_related(
            "user",
            "document",
            "printer",
        )
        .first()
    )


    if not job:

        return Response({
            "message":
                "Print job not found."
        }, status=404)


    payment = getattr(
        job,
        "payment",
        None
    )

    printer = getattr(
        job,
        "printer",
        None
    )


    return Response({
        "success": True,

        "print_job": {
            "id": job.id,

            "customer": {
                "id":
                    job.user.id,

                "name":
                    job.user.full_name,

                "email":
                    job.user.email,

                "phone_number":
                    job.user.phone_number,
            },

            "document": {
                "id":
                    job.document.id,

                "name":
                    job.document.original_name,

                "pages":
                    job.document.pages,

                "size":
                    job.document.size,

                "mime_type":
                    job.document.mime_type,

                "url":
                    job.document.cloudinary_url,
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

            "printer":
                {
                    "id":
                        printer.id,

                    "name":
                        printer.name,

                    "system_name":
                        printer.system_name,

                    "status":
                        printer.status,

                    "ip_address":
                        printer.ip_address,
                }
                if printer
                else None,

            "payment":
                {
                    "id":
                        payment.id,

                    "amount":
                        payment.amount,

                    "subtotal":
                        payment.subtotal,

                    "color_charge":
                        payment.color_charge,

                    "paper_charge":
                        payment.paper_charge,

                    "discount":
                        payment.discount,

                    "status":
                        payment.status,

                    "payment_method":
                        payment.payment_method,

                    "transaction_id":
                        payment.transaction_id,

                    "mpesa_receipt_number":
                        payment.mpesa_receipt_number,

                    "paid_at":
                        payment.paid_at,
                }
                if payment
                else None,

            "created_at":
                job.created_at,

            "updated_at":
                job.updated_at,
        }
    })


# ============================================================
# UPDATE PRINT JOB STATUS
# ============================================================

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_business_print_job_status(
    request,
    job_id
):

    user = request.user

    if user.role not in [
        "business_admin",
        "staff",
    ]:
        return Response({
            "message":
                "You are not allowed to update print jobs."
        }, status=403)


    tenant = user.tenant


    job = PrintJob.objects.filter(
        id=job_id,
        tenant=tenant
    ).first()


    if not job:

        return Response({
            "message":
                "Print job not found."
        }, status=404)


    new_status = request.data.get(
        "status"
    )


    allowed_statuses = [
        "queued",
        "printing",
        "printed",
        "failed",
        "cancelled",
    ]


    if new_status not in allowed_statuses:

        return Response({
            "message":
                "Invalid print job status."
        }, status=400)


    # Do not manually print an unpaid job
    if (
        new_status in [
            "queued",
            "printing",
            "printed",
        ]
        and
        hasattr(job, "payment")
        and
        job.payment.status != "paid"
    ):

        return Response({
            "message":
                "This print job has not been paid."
        }, status=400)


    job.status = new_status

    job.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )


    if new_status in [
        "printing",
        "printed",
        "failed",
    ]:

        job.document.status = (
            "printed"
            if new_status == "printed"
            else new_status
        )

        job.document.save(
            update_fields=[
                "status"
            ]
        )


    return Response({
        "success": True,

        "message":
            "Print job status updated successfully.",

        "print_job": {
            "id": job.id,
            "status": job.status,
        }
    })


# ============================================================
# ASSIGN PRINTER
# ============================================================

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def assign_print_job_printer(
    request,
    job_id
):

    user = request.user

    if user.role not in [
        "business_admin",
        "staff",
    ]:

        return Response({
            "message":
                "You are not allowed to assign printers."
        }, status=403)


    tenant = user.tenant


    job = PrintJob.objects.filter(
        id=job_id,
        tenant=tenant
    ).first()


    if not job:

        return Response({
            "message":
                "Print job not found."
        }, status=404)


    printer_id = request.data.get(
        "printer_id"
    )


    printer = Printer.objects.filter(
        id=printer_id,
        tenant=tenant,
        is_active=True
    ).first()


    if not printer:

        return Response({
            "message":
                "Printer not found."
        }, status=404)


    job.printer = printer

    job.save(
        update_fields=[
            "printer",
            "updated_at",
        ]
    )


    return Response({
        "success": True,

        "message":
            "Printer assigned successfully.",

        "printer": {
            "id":
                printer.id,

            "name":
                printer.name,

            "status":
                printer.status,
        }
    })