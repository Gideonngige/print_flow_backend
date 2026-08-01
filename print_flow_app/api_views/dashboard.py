# print_flow_app/api_views/dashboard.py
from .common_imports import *



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_dashboard(request):
    user = request.user

    # Dashboard statistics
    total_documents = Document.objects.filter(
        user=user
    ).count()

    completed_jobs = PrintJob.objects.filter(
        user=user,
        status="printed",
    ).count()

    printing_jobs = PrintJob.objects.filter(
        user=user,
        status="printing",
    ).count()

    queued_jobs = PrintJob.objects.filter(
        user=user,
        status="queued",
    ).count()

    total_spent = (
        Payment.objects.filter(
            print_job__user=user,
            status="paid",
        ).aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )

    # Get the most recent five print jobs
    recent_jobs = (
        PrintJob.objects.filter(user=user)
        .select_related("document")
        .prefetch_related("payment")
        .order_by("-created_at")[:5]
    )

    jobs_data = []

    for job in recent_jobs:
        try:
            payment = job.payment
        except Payment.DoesNotExist:
            payment = None

        jobs_data.append({
            "id": job.id,
            "name": job.document.original_name,
            "pages": job.document.pages,
            "copies": job.copies,
            "paper_size": job.paper_size,
            "color": job.color,
            "double_sided": job.double_sided,
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

    full_name = (
        getattr(user, "full_name", None)
        or user.get_full_name()
        or getattr(user, "username", None)
        or user.email
    )

    return Response({
        "success": True,
        "user": {
            "id": user.id,
            "name": full_name,
            "email": user.email,
        },
        "statistics": {
            "total_documents": total_documents,
            "completed_jobs": completed_jobs,
            "printing_jobs": printing_jobs,
            "queued_jobs": queued_jobs,
            "total_spent": str(total_spent),
        },
        "recent_jobs": jobs_data,
    })