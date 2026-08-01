from .permissions import IsAdminUserRole
from .common_imports import *


@api_view(["GET"])
@permission_classes([IsAdminUserRole])
def admin_dashboard(request):
    today = timezone.now().date()
    last_7_days = timezone.now() - timedelta(days=7)

    total_users = User.objects.filter(
        role="user"
    ).count()

    total_documents = Document.objects.count()

    total_jobs = PrintJob.objects.count()

    queued_jobs = PrintJob.objects.filter(
        status="queued"
    ).count()

    printing_jobs = PrintJob.objects.filter(
        status="printing"
    ).count()

    completed_jobs = PrintJob.objects.filter(
        status="printed"
    ).count()

    failed_jobs = PrintJob.objects.filter(
        status="failed"
    ).count()

    successful_payments = Payment.objects.filter(
        status="paid"
    )

    total_revenue = (
        successful_payments.aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    today_revenue = (
        successful_payments.filter(
            paid_at__date=today
        ).aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    weekly_revenue = (
        successful_payments.filter(
            paid_at__gte=last_7_days
        ).aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    recent_jobs = (
        PrintJob.objects
        .select_related(
            "user",
            "document",
            "payment",
        )
        .order_by("-created_at")[:8]
    )

    recent_jobs_data = []

    for job in recent_jobs:
        try:
            payment = job.payment
        except Payment.DoesNotExist:
            payment = None

        recent_jobs_data.append({
            "id": job.id,
            "order_number": f"PF-{job.id:04d}",
            "customer": {
                "id": job.user.id,
                "name": (
                    getattr(job.user, "full_name", None)
                    or job.user.get_full_name()
                    or job.user.email
                ),
                "email": job.user.email,
            },
            "document": job.document.original_name,
            "pages": job.document.pages,
            "copies": job.copies,
            "status": job.status,
            "amount": (
                str(payment.amount)
                if payment
                else "0.00"
            ),
            "payment_status": (
                payment.status
                if payment
                else "not_created"
            ),
            "created_at": job.created_at,
        })

    return Response({
        "success": True,
        "statistics": {
            "total_users": total_users,
            "total_documents": total_documents,
            "total_jobs": total_jobs,
            "queued_jobs": queued_jobs,
            "printing_jobs": printing_jobs,
            "completed_jobs": completed_jobs,
            "failed_jobs": failed_jobs,
            "total_revenue": str(total_revenue),
            "today_revenue": str(today_revenue),
            "weekly_revenue": str(weekly_revenue),
        },
        "recent_jobs": recent_jobs_data,
    })



@api_view(["GET"])
@permission_classes([IsAdminUserRole])
def admin_users(request):
    search = request.GET.get("search", "").strip()
    role = request.GET.get("role", "").strip()

    users = User.objects.all().order_by("-date_joined")

    if search:
        users = users.filter(
            Q(email__icontains=search)
            | Q(username__icontains=search)
            | Q(full_name__icontains=search)
        )

    if role:
        users = users.filter(role=role)

    users_data = []

    for user in users:
        users_data.append({
            "id": user.id,
            "name": (
                getattr(user, "full_name", None)
                or user.get_full_name()
                or getattr(user, "username", None)
                or user.email
            ),
            "email": user.email,
            "phone": getattr(user, "phone", None),
            "role": user.role,
            "is_active": user.is_active,
            "date_joined": user.date_joined,
            "documents": Document.objects.filter(
                user=user
            ).count(),
            "print_jobs": PrintJob.objects.filter(
                user=user
            ).count(),
            "total_spent": str(
                Payment.objects.filter(
                    print_job__user=user,
                    status="paid",
                ).aggregate(
                    total=Sum("amount")
                )["total"]
                or Decimal("0.00")
            ),
        })

    return Response({
        "success": True,
        "count": len(users_data),
        "users": users_data,
    })



@api_view(["PATCH"])
@permission_classes([IsAdminUserRole])
def update_user_status(request, user_id):
    user = User.objects.filter(
        id=user_id
    ).first()

    if not user:
        return Response({
            "success": False,
            "message": "User not found.",
        }, status=404)

    if user.id == request.user.id:
        return Response({
            "success": False,
            "message": "You cannot suspend your own account.",
        }, status=400)

    is_active = request.data.get("is_active")

    if not isinstance(is_active, bool):
        return Response({
            "success": False,
            "message": "is_active must be true or false.",
        }, status=400)

    user.is_active = is_active
    user.save(update_fields=["is_active"])

    return Response({
        "success": True,
        "message": (
            "User activated successfully."
            if is_active
            else "User suspended successfully."
        ),
        "user": {
            "id": user.id,
            "is_active": user.is_active,
        },
    })


@api_view(["GET"])
@permission_classes([IsAdminUserRole])
def admin_print_jobs(request):
    search = request.GET.get("search", "").strip()
    job_status = request.GET.get("status", "").strip()

    jobs = (
        PrintJob.objects
        .select_related(
            "user",
            "document",
            "payment",
        )
        .order_by("-created_at")
    )

    if search:
        jobs = jobs.filter(
            Q(document__original_name__icontains=search)
            | Q(user__email__icontains=search)
        )

    if job_status:
        jobs = jobs.filter(status=job_status)

    jobs_data = []

    for job in jobs:
        try:
            payment = job.payment
        except Payment.DoesNotExist:
            payment = None

        jobs_data.append({
            "id": job.id,
            "order_number": f"PF-{job.id:04d}",
            "customer": {
                "id": job.user.id,
                "name": (
                    getattr(job.user, "full_name", None)
                    or job.user.get_full_name()
                    or job.user.email
                ),
                "email": job.user.email,
            },
            "document": {
                "id": job.document.id,
                "name": job.document.original_name,
                "pages": job.document.pages,
                "url": job.document.cloudinary_url,
            },
            "copies": job.copies,
            "paper_size": job.paper_size,
            "color": job.color,
            "double_sided": job.double_sided,
            "status": job.status,
            "payment": {
                "id": payment.id if payment else None,
                "amount": str(payment.amount) if payment else "0.00",
                "status": payment.status if payment else "not_created",
                "receipt": (
                    payment.mpesa_receipt_number
                    if payment
                    else None
                ),
            },
            "created_at": job.created_at,
            "updated_at": job.updated_at,
        })

    return Response({
        "success": True,
        "count": len(jobs_data),
        "jobs": jobs_data,
    })


@api_view(["PATCH"])
@permission_classes([IsAdminUserRole])
def admin_update_print_job(request, print_job_id):
    job = PrintJob.objects.select_related(
        "document"
    ).filter(
        id=print_job_id
    ).first()

    if not job:
        return Response({
            "success": False,
            "message": "Print job not found.",
        }, status=404)

    new_status = request.data.get("status")

    allowed_statuses = [
        "pending",
        "paid",
        "queued",
        "printing",
        "printed",
        "failed",
    ]

    if new_status not in allowed_statuses:
        return Response({
            "success": False,
            "message": "Invalid print job status.",
        }, status=400)

    job.status = new_status
    job.save(update_fields=["status", "updated_at"])

    if new_status == "printing":
        job.document.status = "printing"
    elif new_status == "printed":
        job.document.status = "printed"
    elif new_status in ["queued", "paid"]:
        job.document.status = "pending"

    job.document.save(update_fields=["status"])

    return Response({
        "success": True,
        "message": "Print job status updated.",
        "status": job.status,
    })


@api_view(["POST"])
@permission_classes([IsAdminUserRole])
def retry_print_job(request, print_job_id):
    job = PrintJob.objects.filter(
        id=print_job_id
    ).first()

    if not job:
        return Response({
            "success": False,
            "message": "Print job not found.",
        }, status=404)

    try:
        payment = job.payment
    except Payment.DoesNotExist:
        return Response({
            "success": False,
            "message": "Payment record not found.",
        }, status=404)

    if payment.status != "paid":
        return Response({
            "success": False,
            "message": "Only paid jobs can be retried.",
        }, status=400)

    job.status = "queued"
    job.save(update_fields=["status", "updated_at"])

    return Response({
        "success": True,
        "message": "Print job has been returned to the queue.",
    })



@api_view(["GET"])
@permission_classes([IsAdminUserRole])
def admin_payments(request):
    search = request.GET.get("search", "").strip()
    payment_status = request.GET.get("status", "").strip()
    method = request.GET.get("method", "").strip()

    payments = (
        Payment.objects
        .select_related(
            "print_job",
            "print_job__user",
            "print_job__document",
        )
        .order_by("-id")
    )

    if search:
        payments = payments.filter(
            Q(print_job__user__email__icontains=search)
            | Q(
                print_job__document__original_name__icontains=search
            )
            | Q(mpesa_receipt_number__icontains=search)
            | Q(transaction_id__icontains=search)
        )

    if payment_status:
        payments = payments.filter(
            status=payment_status
        )

    if method:
        payments = payments.filter(
            payment_method=method
        )

    payments_data = []

    for payment in payments:
        job = payment.print_job

        payments_data.append({
            "id": payment.id,
            "order_number": f"PF-{job.id:04d}",
            "customer": {
                "id": job.user.id,
                "name": (
                    getattr(job.user, "full_name", None)
                    or job.user.get_full_name()
                    or job.user.email
                ),
                "email": job.user.email,
            },
            "document": job.document.original_name,
            "subtotal": str(payment.subtotal),
            "paper_charge": str(payment.paper_charge),
            "color_charge": str(payment.color_charge),
            "discount": str(payment.discount),
            "amount": str(payment.amount),
            "payment_method": payment.payment_method,
            "status": payment.status,
            "transaction_id": payment.transaction_id,
            "mpesa_receipt_number": (
                payment.mpesa_receipt_number
            ),
            "checkout_request_id": (
                payment.checkout_request_id
            ),
            "paid_at": payment.paid_at,
        })

    total_paid = (
        payments.filter(
            status="paid"
        ).aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )

    return Response({
        "success": True,
        "count": len(payments_data),
        "total_paid": str(total_paid),
        "payments": payments_data,
    })



@api_view(["GET"])
@permission_classes([IsAdminUserRole])
def admin_documents(request):
    search = request.GET.get("search", "").strip()

    documents = (
        Document.objects
        .select_related("user")
        .order_by("-uploaded_at")
    )

    if search:
        documents = documents.filter(
            Q(original_name__icontains=search)
            | Q(user__email__icontains=search)
        )

    documents_data = []

    for document in documents:
        documents_data.append({
            "id": document.id,
            "name": document.original_name,
            "pages": document.pages,
            "size": document.size,
            "mime_type": document.mime_type,
            "status": document.status,
            "url": document.cloudinary_url,
            "uploaded_at": document.uploaded_at,
            "owner": {
                "id": document.user.id,
                "name": (
                    getattr(document.user, "full_name", None)
                    or document.user.get_full_name()
                    or document.user.email
                ),
                "email": document.user.email,
            },
        })

    return Response({
        "success": True,
        "count": len(documents_data),
        "documents": documents_data,
    })






