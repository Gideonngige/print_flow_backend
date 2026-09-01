from .common_imports import *


# ============================================================
# BUSINESS SUBSCRIPTION OVERVIEW
# ============================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def business_subscription(request):

    user = request.user

    if user.role not in [
        "business_admin",
        "staff",
    ]:
        return Response({
            "message":
                "You are not allowed to access subscription information."
        }, status=403)

    tenant = user.tenant

    if not tenant:
        return Response({
            "message":
                "Your account is not linked to a business."
        }, status=400)

    subscription = (
        Subscription.objects
        .select_related("plan")
        .filter(
            tenant=tenant
        )
        .first()
    )

    if not subscription:
        return Response({
            "message":
                "No subscription was found for this business."
        }, status=404)

    plan = subscription.plan

    # --------------------------------------------------------
    # Usage
    # --------------------------------------------------------

    used_users = User.objects.filter(
        tenant=tenant
    ).exclude(
        role="platform_admin"
    ).count()

    used_documents = Document.objects.filter(
        tenant=tenant
    ).count()

    used_print_jobs = PrintJob.objects.filter(
        tenant=tenant
    ).count()

    total_storage_bytes = (
        Document.objects
        .filter(
            tenant=tenant
        )
        .aggregate(
            total=Sum("size")
        )["total"]
        or 0
    )

    total_storage_mb = (
        Decimal(total_storage_bytes)
        / Decimal(1024 * 1024)
    )

    # --------------------------------------------------------
    # Remaining days
    # --------------------------------------------------------

    days_remaining = None

    if subscription.current_period_end:
        difference = (
            subscription.current_period_end
            - timezone.now()
        )

        days_remaining = max(
            difference.days,
            0
        )

    trial_days_remaining = None

    if subscription.trial_end:
        difference = (
            subscription.trial_end
            - timezone.now()
        )

        trial_days_remaining = max(
            difference.days,
            0
        )

    # --------------------------------------------------------
    # Payment history
    # --------------------------------------------------------

    payments = (
        SubscriptionPayment.objects
        .filter(
            tenant=tenant,
            subscription=subscription
        )
        .order_by(
            "-created_at"
        )[:20]
    )

    payments_data = []

    for payment in payments:

        payments_data.append({
            "id":
                payment.id,

            "amount":
                payment.amount,

            "currency":
                payment.currency,

            "payment_method":
                payment.payment_method,

            "phone_number":
                payment.phone_number,

            "status":
                payment.status,

            "transaction_id":
                payment.transaction_id,

            "mpesa_receipt_number":
                payment.mpesa_receipt_number,

            "checkout_request_id":
                payment.checkout_request_id,

            "provider_reference":
                payment.provider_reference,

            "period_start":
                payment.period_start,

            "period_end":
                payment.period_end,

            "paid_at":
                payment.paid_at,

            "created_at":
                payment.created_at,
        })

    # --------------------------------------------------------
    # Available plans
    # --------------------------------------------------------

    available_plans = (
        Plan.objects
        .filter(
            is_active=True
        )
        .order_by(
            "monthly_price"
        )
    )

    plan_data = []

    for item in available_plans:

        plan_data.append({
            "id":
                item.id,

            "name":
                item.name,

            "slug":
                item.slug,

            "description":
                item.description,

            "monthly_price":
                item.monthly_price,

            "yearly_price":
                item.yearly_price,

            "max_users":
                item.max_users,

            "max_documents":
                item.max_documents,

            "max_print_jobs":
                item.max_print_jobs,

            "max_storage_mb":
                item.max_storage_mb,

            "allow_color_printing":
                item.allow_color_printing,

            "allow_double_sided":
                item.allow_double_sided,

            "allow_multiple_printers":
                item.allow_multiple_printers,

            "allow_staff_accounts":
                item.allow_staff_accounts,

            "allow_custom_domain":
                item.allow_custom_domain,

            "advanced_reports":
                item.advanced_reports,

            "api_access":
                item.api_access,

            "priority_support":
                item.priority_support,

            "is_popular":
                item.is_popular,
        })

    return Response({
        "success": True,

        "subscription": {
            "id":
                subscription.id,

            "status":
                subscription.status,

            "billing_cycle":
                subscription.billing_cycle,

            "start_date":
                subscription.start_date,

            "current_period_start":
                subscription.current_period_start,

            "current_period_end":
                subscription.current_period_end,

            "trial_start":
                subscription.trial_start,

            "trial_end":
                subscription.trial_end,

            "days_remaining":
                days_remaining,

            "trial_days_remaining":
                trial_days_remaining,

            "auto_renew":
                subscription.auto_renew,

            "payment_method":
                subscription.payment_method,

            "plan": {
                "id":
                    plan.id,

                "name":
                    plan.name,

                "slug":
                    plan.slug,

                "description":
                    plan.description,

                "monthly_price":
                    plan.monthly_price,

                "yearly_price":
                    plan.yearly_price,

                "max_users":
                    plan.max_users,

                "max_documents":
                    plan.max_documents,

                "max_print_jobs":
                    plan.max_print_jobs,

                "max_storage_mb":
                    plan.max_storage_mb,
            }
        },

        "usage": {
            "users": {
                "used":
                    used_users,

                "limit":
                    plan.max_users,
            },

            "documents": {
                "used":
                    used_documents,

                "limit":
                    plan.max_documents,
            },

            "print_jobs": {
                "used":
                    used_print_jobs,

                "limit":
                    plan.max_print_jobs,
            },

            "storage": {
                "used_mb":
                    round(
                        float(
                            total_storage_mb
                        ),
                        2
                    ),

                "limit_mb":
                    plan.max_storage_mb,
            }
        },

        "payments":
            payments_data,

        "available_plans":
            plan_data,
    })


# ============================================================
# CHANGE PLAN
# ============================================================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_business_plan(request):

    user = request.user

    if user.role != "business_admin":
        return Response({
            "message":
                "Only the business administrator can change subscription plans."
        }, status=403)

    tenant = user.tenant

    subscription = (
        Subscription.objects
        .select_related("plan")
        .filter(
            tenant=tenant
        )
        .first()
    )

    if not subscription:
        return Response({
            "message":
                "Subscription not found."
        }, status=404)

    plan_id = request.data.get(
        "plan_id"
    )

    billing_cycle = request.data.get(
        "billing_cycle",
        subscription.billing_cycle
    )

    if billing_cycle not in [
        "monthly",
        "yearly",
    ]:
        return Response({
            "message":
                "Billing cycle must be monthly or yearly."
        }, status=400)

    plan = Plan.objects.filter(
        id=plan_id,
        is_active=True
    ).first()

    if not plan:
        return Response({
            "message":
                "Selected plan was not found."
        }, status=404)

    if (
        plan.id ==
        subscription.plan_id
        and
        billing_cycle ==
        subscription.billing_cycle
    ):
        return Response({
            "message":
                "You are already using this plan and billing cycle."
        }, status=400)

    # For now we only record the requested change.
    # Actual activation should happen after subscription payment succeeds.

    amount = (
        plan.monthly_price
        if billing_cycle == "monthly"
        else plan.yearly_price
    )

    payment = SubscriptionPayment.objects.create(
        subscription=subscription,
        tenant=tenant,
        amount=amount,
        currency="KES",
        payment_method="m-pesa",
        status="pending",
    )

    return Response({
        "success": True,

        "message":
            "Plan change initiated. Complete payment to activate the new plan.",

        "pending_plan": {
            "id":
                plan.id,

            "name":
                plan.name,

            "billing_cycle":
                billing_cycle,

            "amount":
                amount,
        },

        "subscription_payment": {
            "id":
                payment.id,

            "amount":
                payment.amount,

            "status":
                payment.status,
        }
    }, status=201)


# ============================================================
# AUTO RENEW
# ============================================================

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_subscription_auto_renew(request):

    user = request.user

    if user.role != "business_admin":
        return Response({
            "message":
                "Only the business administrator can change auto-renew settings."
        }, status=403)

    tenant = user.tenant

    subscription = Subscription.objects.filter(
        tenant=tenant
    ).first()

    if not subscription:
        return Response({
            "message":
                "Subscription not found."
        }, status=404)

    auto_renew = request.data.get(
        "auto_renew"
    )

    if not isinstance(
        auto_renew,
        bool
    ):
        return Response({
            "message":
                "auto_renew must be true or false."
        }, status=400)

    subscription.auto_renew = auto_renew

    subscription.save(
        update_fields=[
            "auto_renew",
            "updated_at",
        ]
    )

    return Response({
        "success": True,

        "message":
            "Auto-renew setting updated successfully.",

        "auto_renew":
            subscription.auto_renew,
    })