from .common_imports import *


# ============================================================
# PLATFORM ADMIN GUARD
# ============================================================

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
# BOOLEAN HELPER
# ============================================================

def parse_boolean(
    value,
    default=False
):
    if isinstance(
        value,
        bool
    ):
        return value

    if value is None:
        return default

    if isinstance(
        value,
        str
    ):
        normalized = (
            value.strip().lower()
        )

        if normalized in [
            "true",
            "1",
            "yes",
            "on",
        ]:
            return True

        if normalized in [
            "false",
            "0",
            "no",
            "off",
        ]:
            return False

    return bool(value)


# ============================================================
# SERIALIZE SUBSCRIPTION
# ============================================================

def serialize_subscription(
    subscription,
    include_payment_data=True
):
    plan = (
        subscription.plan
    )

    data = {
        "id":
            subscription.id,

        "tenant": {
            "id":
                subscription.tenant.id,

            "name":
                subscription.tenant.name,

            "slug":
                subscription.tenant.slug,

            "email":
                subscription.tenant.email,

            "phone_number":
                subscription.tenant.phone_number,

            "is_active":
                subscription.tenant.is_active,
        },

        "plan": {
            "id":
                plan.id,

            "name":
                plan.name,

            "slug":
                plan.slug,

            "monthly_price":
                plan.monthly_price,

            "yearly_price":
                plan.yearly_price,
        },

        "billing_cycle":
            getattr(
                subscription,
                "billing_cycle",
                None
            ),

        "status":
            subscription.status,

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

        "cancelled_at":
            subscription.cancelled_at,

        "auto_renew":
            subscription.auto_renew,

        "payment_method":
            subscription.payment_method,

        "created_at":
            subscription.created_at,

        "updated_at":
            subscription.updated_at,
    }

    if include_payment_data:

        total_paid = (
            SubscriptionPayment.objects
            .filter(
                subscription=
                    subscription,

                status="paid"
            )
            .aggregate(
                total=Sum(
                    "amount"
                )
            )["total"]
            or Decimal("0.00")
        )

        latest_payment = (
            SubscriptionPayment.objects
            .filter(
                subscription=
                    subscription
            )
            .order_by(
                "-created_at"
            )
            .first()
        )

        data["total_paid"] = (
            total_paid
        )

        data["latest_payment"] = (
            {
                "id":
                    latest_payment.id,

                "amount":
                    latest_payment.amount,

                "currency":
                    latest_payment.currency,

                "status":
                    latest_payment.status,

                "payment_method":
                    latest_payment.payment_method,

                "transaction_id":
                    latest_payment.transaction_id,

                "mpesa_receipt_number":
                    latest_payment.mpesa_receipt_number,

                "paid_at":
                    latest_payment.paid_at,

                "created_at":
                    latest_payment.created_at,
            }
            if latest_payment
            else None
        )

    return data


# ============================================================
# LIST SUBSCRIPTIONS
# ============================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def platform_subscriptions(request):

    error_response = (
        ensure_platform_admin(
            request
        )
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
            .lower()
        )

        plan_slug = (
            request.query_params
            .get(
                "plan",
                ""
            )
            .strip()
        )

        billing_cycle = (
            request.query_params
            .get(
                "billing_cycle",
                ""
            )
            .strip()
            .lower()
        )

        subscriptions = (
            Subscription.objects
            .select_related(
                "tenant",
                "plan"
            )
            .all()
            .order_by(
                "-created_at"
            )
        )

        # ====================================================
        # SEARCH
        # ====================================================

        if search:

            subscriptions = (
                subscriptions
                .filter(
                    Q(
                        tenant__name__icontains=
                            search
                    )
                    |
                    Q(
                        tenant__email__icontains=
                            search
                    )
                    |
                    Q(
                        tenant__slug__icontains=
                            search
                    )
                    |
                    Q(
                        plan__name__icontains=
                            search
                    )
                )
            )

        # ====================================================
        # STATUS
        # ====================================================

        if status_filter:

            subscriptions = (
                subscriptions
                .filter(
                    status=
                        status_filter
                )
            )

        # ====================================================
        # PLAN
        # ====================================================

        if plan_slug:

            subscriptions = (
                subscriptions
                .filter(
                    plan__slug=
                        plan_slug
                )
            )

        # ====================================================
        # BILLING CYCLE
        # ====================================================

        if billing_cycle:

            if billing_cycle not in [
                "monthly",
                "yearly",
            ]:
                return Response({
                    "success": False,
                    "message":
                        "Invalid billing cycle."
                }, status=400)

            if hasattr(
                Subscription,
                "billing_cycle"
            ):
                subscriptions = (
                    subscriptions
                    .filter(
                        billing_cycle=
                            billing_cycle
                    )
                )

        subscriptions = (
            subscriptions.distinct()
        )

        subscriptions_data = [
            serialize_subscription(
                subscription
            )
            for subscription
            in subscriptions
        ]

        # ====================================================
        # STATS
        # ====================================================

        stats = {
            "total":
                Subscription.objects
                .count(),

            "active":
                Subscription.objects
                .filter(
                    status="active"
                )
                .count(),

            "trial":
                Subscription.objects
                .filter(
                    status="trial"
                )
                .count(),

            "past_due":
                Subscription.objects
                .filter(
                    status="past_due"
                )
                .count(),

            "expired":
                Subscription.objects
                .filter(
                    status="expired"
                )
                .count(),

            "cancelled":
                Subscription.objects
                .filter(
                    status="cancelled"
                )
                .count(),

            "suspended":
                Subscription.objects
                .filter(
                    status="suspended"
                )
                .count(),
        }

        return Response({
            "success": True,

            "count":
                len(
                    subscriptions_data
                ),

            "stats":
                stats,

            "subscriptions":
                subscriptions_data,
        })

    except Exception as error:

        print(
            "PLATFORM SUBSCRIPTIONS ERROR:",
            error
        )

        return Response({
            "success": False,
            "message":
                "Unable to load subscriptions."
        }, status=500)


# ============================================================
# UPDATE SUBSCRIPTION
# ============================================================

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def platform_update_subscription(
    request,
    subscription_id
):

    error_response = (
        ensure_platform_admin(
            request
        )
    )

    if error_response:
        return error_response

    subscription = (
        Subscription.objects
        .select_related(
            "tenant",
            "plan"
        )
        .filter(
            id=subscription_id
        )
        .first()
    )

    if not subscription:

        return Response({
            "success": False,
            "message":
                "Subscription not found."
        }, status=404)

    data = request.data

    # ========================================================
    # PLAN
    # ========================================================

    if "plan_id" in data:

        plan = (
            Plan.objects
            .filter(
                id=data.get(
                    "plan_id"
                ),
                is_active=True
            )
            .first()
        )

        if not plan:

            return Response({
                "success": False,
                "message":
                    (
                        "Selected plan was not "
                        "found or is inactive."
                    )
            }, status=404)

        subscription.plan = (
            plan
        )

    # ========================================================
    # BILLING CYCLE
    # ========================================================

    if "billing_cycle" in data:

        billing_cycle = (
            str(
                data.get(
                    "billing_cycle",
                    ""
                )
            )
            .strip()
            .lower()
        )

        if billing_cycle not in [
            "monthly",
            "yearly",
        ]:

            return Response({
                "success": False,
                "message":
                    "Invalid billing cycle."
            }, status=400)

        if hasattr(
            subscription,
            "billing_cycle"
        ):
            subscription.billing_cycle = (
                billing_cycle
            )

    # ========================================================
    # STATUS
    # ========================================================

    if "status" in data:

        allowed_statuses = [
            choice[0]
            for choice
            in Subscription.STATUS_CHOICES
        ]

        status_value = (
            str(
                data.get(
                    "status",
                    ""
                )
            )
            .strip()
        )

        if (
            status_value
            not in allowed_statuses
        ):

            return Response({
                "success": False,
                "message":
                    "Invalid subscription status."
            }, status=400)

        subscription.status = (
            status_value
        )

        if (
            status_value ==
            "cancelled"
        ):

            if (
                not subscription.cancelled_at
            ):
                subscription.cancelled_at = (
                    timezone.now()
                )

        else:

            subscription.cancelled_at = (
                None
            )

    # ========================================================
    # AUTO RENEW
    # ========================================================

    if "auto_renew" in data:

        subscription.auto_renew = (
            parse_boolean(
                data.get(
                    "auto_renew"
                ),
                subscription.auto_renew
            )
        )

    # ========================================================
    # PERIOD START
    # ========================================================

    if "current_period_start" in data:

        value = (
            data.get(
                "current_period_start"
            )
        )

        parsed_date = (
            parse_subscription_datetime(
                value
            )
        )

        if not parsed_date:

            return Response({
                "success": False,
                "message":
                    "Invalid period start date."
            }, status=400)

        subscription.current_period_start = (
            parsed_date
        )

    # ========================================================
    # PERIOD END
    # ========================================================

    if "current_period_end" in data:

        value = (
            data.get(
                "current_period_end"
            )
        )

        parsed_date = (
            parse_subscription_datetime(
                value
            )
        )

        if not parsed_date:

            return Response({
                "success": False,
                "message":
                    "Invalid period end date."
            }, status=400)

        subscription.current_period_end = (
            parsed_date
        )

    # ========================================================
    # VALIDATE PERIOD
    # ========================================================

    if (
        subscription.current_period_start
        and
        subscription.current_period_end
        and
        subscription.current_period_end
        <=
        subscription.current_period_start
    ):

        return Response({
            "success": False,
            "message":
                (
                    "Subscription period end "
                    "must be after the start date."
                )
        }, status=400)

    # ========================================================
    # SAVE
    # ========================================================

    try:
        subscription.save()

        return Response({
            "success": True,

            "message":
                "Subscription updated successfully.",

            "subscription":
                serialize_subscription(
                    subscription
                ),
        })

    except Exception as error:

        print(
            "UPDATE SUBSCRIPTION ERROR:",
            error
        )

        return Response({
            "success": False,
            "message":
                "Unable to update subscription."
        }, status=500)


# ============================================================
# EXTEND SUBSCRIPTION
# ============================================================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def platform_extend_subscription(
    request,
    subscription_id
):

    error_response = (
        ensure_platform_admin(
            request
        )
    )

    if error_response:
        return error_response

    subscription = (
        Subscription.objects
        .select_related(
            "tenant",
            "plan"
        )
        .filter(
            id=subscription_id
        )
        .first()
    )

    if not subscription:

        return Response({
            "success": False,
            "message":
                "Subscription not found."
        }, status=404)

    days = (
        request.data.get(
            "days",
            30
        )
    )

    try:
        days = int(
            days
        )

    except (
        TypeError,
        ValueError
    ):

        return Response({
            "success": False,
            "message":
                "Days must be a valid number."
        }, status=400)

    if (
        days < 1
        or
        days > 3650
    ):

        return Response({
            "success": False,
            "message":
                (
                    "Extension must be between "
                    "1 and 3650 days."
                )
        }, status=400)

    now = (
        timezone.now()
    )

    base_date = (
        subscription.current_period_end
        if (
            subscription.current_period_end
            and
            subscription.current_period_end >
            now
        )
        else now
    )

    subscription.current_period_end = (
        base_date
        +
        datetime.timedelta(
            days=days
        )
    )

    if subscription.status in [
        "expired",
        "past_due",
        "suspended",
    ]:

        subscription.status = (
            "active"
        )

        subscription.cancelled_at = (
            None
        )

    try:
        subscription.save()

        return Response({
            "success": True,

            "message":
                (
                    f"Subscription extended "
                    f"by {days} days."
                ),

            "subscription":
                serialize_subscription(
                    subscription
                ),
        })

    except Exception as error:

        print(
            "EXTEND SUBSCRIPTION ERROR:",
            error
        )

        return Response({
            "success": False,
            "message":
                "Unable to extend subscription."
        }, status=500)


# ============================================================
# DATE PARSER
# ============================================================

def parse_subscription_datetime(
    value
):
    if not value:
        return None

    try:
        parsed_date = (
            datetime.datetime
            .fromisoformat(
                str(
                    value
                ).replace(
                    "Z",
                    "+00:00"
                )
            )
        )

        if timezone.is_naive(
            parsed_date
        ):
            parsed_date = (
                timezone.make_aware(
                    parsed_date
                )
            )

        return parsed_date

    except (
        ValueError,
        TypeError
    ):
        return None