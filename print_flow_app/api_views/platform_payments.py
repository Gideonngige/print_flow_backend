from .common_imports import *


def ensure_platform_admin(request):
    user = request.user

    if (
        not user.is_authenticated
        or user.role != "platform_admin"
    ):
        return Response({
            "success": False,
            "message":
                "You are not allowed to access this resource."
        }, status=403)

    return None


# ============================================================
# LIST SUBSCRIPTION PAYMENTS
# ============================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def platform_subscription_payments(request):

    error_response = ensure_platform_admin(
        request
    )

    if error_response:
        return error_response

    try:
        search = (
            request.query_params
            .get(
                "search",
                ""
            )
            .strip()
        )

        status_filter = (
            request.query_params
            .get(
                "status",
                ""
            )
            .strip()
        )

        payment_method = (
            request.query_params
            .get(
                "payment_method",
                ""
            )
            .strip()
        )

        payments = (
            SubscriptionPayment.objects
            .select_related(
                "tenant",
                "subscription",
                "subscription__plan",
            )
            .all()
            .order_by(
                "-created_at"
            )
        )


        # ----------------------------------------------------
        # Search
        # ----------------------------------------------------

        if search:
            payments = payments.filter(
                Q(
                    tenant__name__icontains=search
                )
                |
                Q(
                    tenant__email__icontains=search
                )
                |
                Q(
                    transaction_id__icontains=search
                )
                |
                Q(
                    mpesa_receipt_number__icontains=search
                )
                |
                Q(
                    provider_reference__icontains=search
                )
            )


        # ----------------------------------------------------
        # Status
        # ----------------------------------------------------

        if status_filter:
            payments = payments.filter(
                status=status_filter
            )


        # ----------------------------------------------------
        # Payment Method
        # ----------------------------------------------------

        if payment_method:
            payments = payments.filter(
                payment_method=payment_method
            )


        payments_data = []


        for payment in payments:

            payments_data.append({
                "id":
                    payment.id,

                "tenant": {
                    "id":
                        payment.tenant.id,

                    "name":
                        payment.tenant.name,

                    "slug":
                        payment.tenant.slug,

                    "email":
                        payment.tenant.email,
                },

                "subscription": {
                    "id":
                        payment.subscription.id,

                    "status":
                        payment.subscription.status,

                    "plan": {
                        "id":
                            payment.subscription.plan.id,

                        "name":
                            payment.subscription.plan.name,

                        "slug":
                            payment.subscription.plan.slug,
                    },
                },

                "amount":
                    payment.amount,

                "currency":
                    payment.currency,

                "payment_method":
                    payment.payment_method,

                "phone_number":
                    payment.phone_number,

                "transaction_id":
                    payment.transaction_id,

                "mpesa_receipt_number":
                    payment.mpesa_receipt_number,

                "checkout_request_id":
                    payment.checkout_request_id,

                "merchant_request_id":
                    payment.merchant_request_id,

                "provider_reference":
                    payment.provider_reference,

                "status":
                    payment.status,

                "period_start":
                    payment.period_start,

                "period_end":
                    payment.period_end,

                "paid_at":
                    payment.paid_at,

                "created_at":
                    payment.created_at,

                "updated_at":
                    payment.updated_at,
            })


        # ----------------------------------------------------
        # Stats
        # ----------------------------------------------------

        paid_revenue = (
            SubscriptionPayment.objects
            .filter(
                status="paid"
            )
            .aggregate(
                total=Sum("amount")
            )["total"]
            or Decimal("0.00")
        )


        pending_revenue = (
            SubscriptionPayment.objects
            .filter(
                status="pending"
            )
            .aggregate(
                total=Sum("amount")
            )["total"]
            or Decimal("0.00")
        )


        refunded_revenue = (
            SubscriptionPayment.objects
            .filter(
                status="refunded"
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
                microsecond=0,
            )
        )


        monthly_revenue = (
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


        return Response({
            "success": True,

            "count":
                len(payments_data),

            "stats": {
                "total_payments":
                    SubscriptionPayment.objects.count(),

                "paid_payments":
                    SubscriptionPayment.objects
                    .filter(
                        status="paid"
                    )
                    .count(),

                "pending_payments":
                    SubscriptionPayment.objects
                    .filter(
                        status="pending"
                    )
                    .count(),

                "failed_payments":
                    SubscriptionPayment.objects
                    .filter(
                        status="failed"
                    )
                    .count(),

                "refunded_payments":
                    SubscriptionPayment.objects
                    .filter(
                        status="refunded"
                    )
                    .count(),

                "total_revenue":
                    paid_revenue,

                "monthly_revenue":
                    monthly_revenue,

                "pending_revenue":
                    pending_revenue,

                "refunded_revenue":
                    refunded_revenue,
            },

            "payments":
                payments_data,
        })

    except Exception as error:

        print(
            "PLATFORM PAYMENTS ERROR:",
            error
        )

        return Response({
            "success": False,
            "message":
                "Unable to load subscription payments."
        }, status=500)


# ============================================================
# PAYMENT DETAIL
# ============================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def platform_subscription_payment_detail(
    request,
    payment_id
):

    error_response = ensure_platform_admin(
        request
    )

    if error_response:
        return error_response


    payment = (
        SubscriptionPayment.objects
        .select_related(
            "tenant",
            "subscription",
            "subscription__plan",
        )
        .filter(
            id=payment_id
        )
        .first()
    )


    if not payment:
        return Response({
            "success": False,
            "message":
                "Subscription payment not found."
        }, status=404)


    return Response({
        "success": True,

        "payment": {
            "id":
                payment.id,

            "tenant": {
                "id":
                    payment.tenant.id,

                "name":
                    payment.tenant.name,

                "slug":
                    payment.tenant.slug,

                "email":
                    payment.tenant.email,

                "phone_number":
                    payment.tenant.phone_number,
            },

            "subscription": {
                "id":
                    payment.subscription.id,

                "status":
                    payment.subscription.status,

                "current_period_start":
                    payment.subscription.current_period_start,

                "current_period_end":
                    payment.subscription.current_period_end,

                "plan": {
                    "id":
                        payment.subscription.plan.id,

                    "name":
                        payment.subscription.plan.name,

                    "price":
                        payment.subscription.plan.price,

                    "billing_cycle":
                        payment.subscription.plan.billing_cycle,
                },
            },

            "amount":
                payment.amount,

            "currency":
                payment.currency,

            "payment_method":
                payment.payment_method,

            "phone_number":
                payment.phone_number,

            "transaction_id":
                payment.transaction_id,

            "mpesa_receipt_number":
                payment.mpesa_receipt_number,

            "checkout_request_id":
                payment.checkout_request_id,

            "merchant_request_id":
                payment.merchant_request_id,

            "provider_reference":
                payment.provider_reference,

            "status":
                payment.status,

            "period_start":
                payment.period_start,

            "period_end":
                payment.period_end,

            "paid_at":
                payment.paid_at,

            "created_at":
                payment.created_at,

            "updated_at":
                payment.updated_at,
        }
    })


# ============================================================
# UPDATE PAYMENT STATUS
# ============================================================

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def platform_update_subscription_payment(
    request,
    payment_id
):

    error_response = ensure_platform_admin(
        request
    )

    if error_response:
        return error_response


    payment = (
        SubscriptionPayment.objects
        .select_related(
            "subscription"
        )
        .filter(
            id=payment_id
        )
        .first()
    )


    if not payment:
        return Response({
            "success": False,
            "message":
                "Subscription payment not found."
        }, status=404)


    new_status = (
        request.data.get(
            "status"
        )
    )


    allowed_statuses = [
        choice[0]
        for choice in
        SubscriptionPayment.STATUS_CHOICES
    ]


    if (
        new_status
        not in allowed_statuses
    ):
        return Response({
            "success": False,
            "message":
                "Invalid payment status."
        }, status=400)


    payment.status = (
        new_status
    )


    if (
        new_status == "paid"
        and not payment.paid_at
    ):
        payment.paid_at = (
            timezone.now()
        )


    if (
        new_status != "paid"
    ):
        payment.paid_at = (
            payment.paid_at
        )


    payment.save(
        update_fields=[
            "status",
            "paid_at",
            "updated_at",
        ]
    )


    # --------------------------------------------------------
    # Optional subscription sync
    # --------------------------------------------------------

    subscription = (
        payment.subscription
    )


    if new_status == "paid":

        if subscription.status in [
            "trial",
            "past_due",
            "expired",
            "suspended",
        ]:
            subscription.status = (
                "active"
            )

            subscription.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )


    return Response({
        "success": True,

        "message":
            "Payment status updated successfully.",

        "payment": {
            "id":
                payment.id,

            "status":
                payment.status,

            "paid_at":
                payment.paid_at,
        }
    })