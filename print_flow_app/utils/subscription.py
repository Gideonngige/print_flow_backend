# utils/subscription.py

from django.utils import timezone

from print_flow_app.models import Subscription


def get_tenant_subscription(tenant):
    return (
        Subscription.objects
        .select_related("plan")
        .filter(
            tenant=tenant
        )
        .first()
    )


def subscription_is_active(subscription):
    if not subscription:
        return False

    if subscription.status != "active":
        return False

    if (
        subscription.current_period_end
        and subscription.current_period_end
        <= timezone.now()
    ):
        return False

    return True



def get_subscription_state(tenant):

    subscription = (
        get_tenant_subscription(
            tenant
        )
    )

    if not subscription:
        return {
            "has_subscription": False,
            "is_active": False,
            "is_expired": False,
            "subscription": None,
        }

    expired = (
        subscription.current_period_end
        and subscription.current_period_end
        <= timezone.now()
    )

    active = (
        subscription.status == "active"
        and not expired
    ) 
    print(f"Has subscription: True. Is active: {active}. Is expired: {expired}. Subscription: {subscription}")

    return {
        "has_subscription": True,
        "is_active": active,
        "is_expired": bool(expired),
        "subscription": subscription,
    }