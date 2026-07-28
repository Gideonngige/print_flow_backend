from .common_imports import *


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def platform_dashboard(request):

    user = request.user

    if user.role != "platform_admin":
        return Response({
            "success": False,
            "message":
                "You are not allowed to access the platform dashboard."
        }, status=403)

    # ============================================================
    # TENANTS
    # ============================================================

    total_tenants = (
        Tenant.objects.count()
    )

    active_tenants = (
        Tenant.objects
        .filter(
            is_active=True
        )
        .count()
    )

    inactive_tenants = (
        Tenant.objects
        .filter(
            is_active=False
        )
        .count()
    )

    # ============================================================
    # USERS
    # ============================================================

    total_users = (
        User.objects.count()
    )

    business_admins = (
        User.objects
        .filter(
            role="business_admin"
        )
        .count()
    )

    staff_users = (
        User.objects
        .filter(
            role="staff"
        )
        .count()
    )

    customers = (
        User.objects
        .filter(
            role="customer"
        )
        .count()
    )

    # ============================================================
    # SUBSCRIPTIONS
    # ============================================================

    total_subscriptions = (
        Subscription.objects.count()
    )

    active_subscriptions = (
        Subscription.objects
        .filter(
            status="active"
        )
        .count()
    )

    trial_subscriptions = (
        Subscription.objects
        .filter(
            status="trial"
        )
        .count()
    )

    expired_subscriptions = (
        Subscription.objects
        .filter(
            status="expired"
        )
        .count()
    )

    cancelled_subscriptions = (
        Subscription.objects
        .filter(
            status="cancelled"
        )
        .count()
    )

    suspended_subscriptions = (
        Subscription.objects
        .filter(
            status="suspended"
        )
        .count()
    )

    # ============================================================
    # SUBSCRIPTION REVENUE
    # ============================================================

    total_subscription_revenue = (
        SubscriptionPayment.objects
        .filter(
            status="paid"
        )
        .aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    current_month_start = (
        timezone.now()
        .replace(
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )
    )

    monthly_subscription_revenue = (
        SubscriptionPayment.objects
        .filter(
            status="paid",
            paid_at__gte=
                current_month_start
        )
        .aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    # ============================================================
    # PLATFORM PRINT JOBS
    # ============================================================

    total_print_jobs = (
        PrintJob.objects.count()
    )

    queued_print_jobs = (
        PrintJob.objects
        .filter(
            status="queued"
        )
        .count()
    )

    printing_print_jobs = (
        PrintJob.objects
        .filter(
            status="printing"
        )
        .count()
    )

    printed_jobs = (
        PrintJob.objects
        .filter(
            status="printed"
        )
        .count()
    )

    failed_jobs = (
        PrintJob.objects
        .filter(
            status="failed"
        )
        .count()
    )

    # ============================================================
    # RECENT TENANTS
    # ============================================================

    recent_tenants = (
        Tenant.objects
        .order_by(
            "-created_at"
        )[:5]
    )

    recent_tenants_data = []

    for tenant in recent_tenants:

        subscription = (
            Subscription.objects
            .filter(
                tenant=tenant
            )
            .select_related(
                "plan"
            )
            .first()
        )

        recent_tenants_data.append({
            "id":
                tenant.id,

            "name":
                tenant.name,

            "slug":
                tenant.slug,

            "subdomain":
                tenant.subdomain,

            "email":
                tenant.email,

            "phone_number":
                tenant.phone_number,

            "is_active":
                tenant.is_active,

            "created_at":
                tenant.created_at,

            "subscription": {
                "status":
                    subscription.status,

                "plan": {
                    "id":
                        subscription.plan.id,

                    "name":
                        subscription.plan.name,

                    "slug":
                        subscription.plan.slug,
                },

                "current_period_end":
                    subscription.current_period_end,
            }
            if subscription
            else None,
        })

    # ============================================================
    # RECENT SUBSCRIPTION PAYMENTS
    # ============================================================

    recent_payments = (
        SubscriptionPayment.objects
        .select_related(
            "tenant",
            "subscription",
            "subscription__plan",
        )
        .order_by(
            "-created_at"
        )[:5]
    )

    recent_payments_data = []

    for payment in recent_payments:

        recent_payments_data.append({
            "id":
                payment.id,

            "tenant": {
                "id":
                    payment.tenant.id,

                "name":
                    payment.tenant.name,
            },

            "plan":
                payment.subscription.plan.name,

            "amount":
                payment.amount,

            "currency":
                payment.currency,

            "payment_method":
                payment.payment_method,

            "status":
                payment.status,

            "transaction_id":
                payment.transaction_id,

            "mpesa_receipt_number":
                payment.mpesa_receipt_number,

            "paid_at":
                payment.paid_at,

            "created_at":
                payment.created_at,
        })

    # ============================================================
    # RESPONSE
    # ============================================================

    return Response({
        "success": True,

        "stats": {
            "tenants": {
                "total":
                    total_tenants,

                "active":
                    active_tenants,

                "inactive":
                    inactive_tenants,
            },

            "users": {
                "total":
                    total_users,

                "business_admins":
                    business_admins,

                "staff":
                    staff_users,

                "customers":
                    customers,
            },

            "subscriptions": {
                "total":
                    total_subscriptions,

                "active":
                    active_subscriptions,

                "trial":
                    trial_subscriptions,

                "expired":
                    expired_subscriptions,

                "cancelled":
                    cancelled_subscriptions,

                "suspended":
                    suspended_subscriptions,
            },

            "revenue": {
                "total":
                    total_subscription_revenue,

                "this_month":
                    monthly_subscription_revenue,
            },

            "print_jobs": {
                "total":
                    total_print_jobs,

                "queued":
                    queued_print_jobs,

                "printing":
                    printing_print_jobs,

                "printed":
                    printed_jobs,

                "failed":
                    failed_jobs,
            },
        },

        "recent_tenants":
            recent_tenants_data,

        "recent_payments":
            recent_payments_data,
    })