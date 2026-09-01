from .common_imports import *


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def business_dashboard(request):

    user = request.user

    # Only business users should access this dashboard
    if user.role not in ["business_admin", "staff"]:
        return Response({
            "message": "You are not allowed to access this dashboard."
        }, status=403)

    tenant = user.tenant

    if not tenant:
        return Response({
            "message": "Your account is not linked to a business."
        }, status=400)

    # ---------------------------------------------------------
    # Subscription
    # ---------------------------------------------------------

    subscription = (
        Subscription.objects
        .select_related("plan")
        .filter(tenant=tenant)
        .first()
    )

    subscription_data = None

    if subscription:

        days_remaining = None

        if subscription.current_period_end:
            delta = (
                subscription.current_period_end
                - timezone.now()
            )

            days_remaining = max(
                delta.days,
                0
            )

        subscription_data = {
            "id": subscription.id,
            "status": subscription.status,
            "billing_cycle": subscription.billing_cycle,
            "start_date": subscription.start_date,
            "current_period_start": subscription.current_period_start,
            "current_period_end": subscription.current_period_end,
            "trial_start": subscription.trial_start,
            "trial_end": subscription.trial_end,
            "days_remaining": days_remaining,
            "auto_renew": subscription.auto_renew,

            "plan": {
                "id": subscription.plan.id,
                "name": subscription.plan.name,
                "slug": subscription.plan.slug,
                "monthly_price": subscription.plan.monthly_price,
                "yearly_price": subscription.plan.yearly_price,
                "max_users": subscription.plan.max_users,
                "max_documents": subscription.plan.max_documents,
                "max_print_jobs": subscription.plan.max_print_jobs,
                "max_storage_mb": subscription.plan.max_storage_mb,
            }
        }

    # ---------------------------------------------------------
    # Dashboard statistics
    # ---------------------------------------------------------

    total_documents = Document.objects.filter(
        tenant=tenant
    ).count()

    total_print_jobs = PrintJob.objects.filter(
        tenant=tenant
    ).count()

    total_customers = User.objects.filter(
        tenant=tenant,
        role="customer"
    ).count()

    total_staff = User.objects.filter(
        tenant=tenant,
        role="staff"
    ).count()

    total_printers = Printer.objects.filter(
        tenant=tenant
    ).count()

    online_printers = Printer.objects.filter(
        tenant=tenant,
        status="online",
        is_active=True
    ).count()

    queued_jobs = PrintJob.objects.filter(
        tenant=tenant,
        status="queued"
    ).count()

    printing_jobs = PrintJob.objects.filter(
        tenant=tenant,
        status="printing"
    ).count()

    completed_jobs = PrintJob.objects.filter(
        tenant=tenant,
        status="printed"
    ).count()

    failed_jobs = PrintJob.objects.filter(
        tenant=tenant,
        status="failed"
    ).count()

    pending_jobs = PrintJob.objects.filter(
        tenant=tenant,
        status="pending"
    ).count()

    paid_jobs = PrintJob.objects.filter(
        tenant=tenant,
        status="paid"
    ).count()

    total_revenue = (
        Payment.objects
        .filter(
            tenant=tenant,
            status="paid"
        )
        .aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    # Today's revenue
    today = timezone.localdate()

    today_revenue = (
        Payment.objects
        .filter(
            tenant=tenant,
            status="paid",
            paid_at__date=today
        )
        .aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    # ---------------------------------------------------------
    # Setup / onboarding checks
    # ---------------------------------------------------------

    has_pricing = Pricing.objects.filter(
        tenant=tenant,
        is_active=True
    ).exists()

    has_printer = Printer.objects.filter(
        tenant=tenant,
        is_active=True
    ).exists()

    has_daraja = DarajaConfiguration.objects.filter(
        tenant=tenant,
        is_active=True
    ).exists()

    business_profile_complete = bool(
        tenant.name
        and tenant.email
        and tenant.phone_number
        and tenant.address
    )

    setup_items = [
        {
            "key": "business_profile",
            "title": "Complete business profile",
            "completed": business_profile_complete,
            "path": "/business/settings",
        },
        {
            "key": "pricing",
            "title": "Configure printing prices",
            "completed": has_pricing,
            "path": "/business/pricing",
        },
        {
            "key": "payments",
            "title": "Connect M-Pesa",
            "completed": has_daraja,
            "path": "/business/settings/payments",
        },
        {
            "key": "printer",
            "title": "Add your printer",
            "completed": has_printer,
            "path": "/business/printers",
        },
    ]

    completed_setup = sum(
        1
        for item in setup_items
        if item["completed"]
    )

    setup_progress = int(
        (
            completed_setup
            / len(setup_items)
        )
        * 100
    )

    # ---------------------------------------------------------
    # Recent jobs
    # ---------------------------------------------------------

    recent_jobs = (
        PrintJob.objects
        .filter(
            tenant=tenant
        )
        .select_related(
            "document",
            "user"
        )
        .order_by(
            "-created_at"
        )[:5]
    )

    recent_jobs_data = []

    for job in recent_jobs:

        payment = getattr(
            job,
            "payment",
            None
        )

        recent_jobs_data.append({
            "id": job.id,
            "document": job.document.original_name,
            "customer": job.user.full_name,
            "pages": job.document.pages,
            "copies": job.copies,
            "paper_size": job.paper_size,
            "color": job.color,
            "double_sided": job.double_sided,
            "status": job.status,
            "amount": (
                payment.amount
                if payment
                else Decimal("0.00")
            ),
            "created_at": job.created_at,
        })

    # ---------------------------------------------------------
    # Response
    # ---------------------------------------------------------

    return Response({
        "success": True,

        "business": {
            "id": tenant.id,
            "name": tenant.name,
            "slug": tenant.slug,
            "subdomain": tenant.subdomain,
            "email": tenant.email,
            "phone_number": tenant.phone_number,
            "address": tenant.address,
            "logo": tenant.logo,
            "is_active": tenant.is_active,
        },

        "subscription": subscription_data,

        "stats": {
            "documents": total_documents,
            "print_jobs": total_print_jobs,
            "customers": total_customers,
            "staff": total_staff,
            "printers": total_printers,
            "online_printers": online_printers,
            "pending_jobs": pending_jobs,
            "paid_jobs": paid_jobs,
            "queued_jobs": queued_jobs,
            "printing_jobs": printing_jobs,
            "completed_jobs": completed_jobs,
            "failed_jobs": failed_jobs,
            "total_revenue": total_revenue,
            "today_revenue": today_revenue,
        },

        "setup": {
            "progress": setup_progress,
            "completed": completed_setup,
            "total": len(setup_items),
            "items": setup_items,
        },

        "recent_jobs": recent_jobs_data,
    })