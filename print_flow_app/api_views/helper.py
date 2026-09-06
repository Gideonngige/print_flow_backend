from .common_imports import *
import os
from rest_framework.response import Response

resend.api_key = os.environ.get("RESEND_API_KEY")

def send_email(to_email, subject, html):
    # Debugging logs (similar to your example)
    print(f"Resend from email: {os.environ.get('RESEND_FROM_EMAIL')}")
    
    params = {
        "from": os.environ.get("RESEND_FROM_EMAIL"), # e.g., "support@vincab.services"
        "to": [to_email],
        "subject": subject,
        "html": html,
    }

    try:
        email = resend.Emails.send(params)
        print(f"Email sent! ID: {email['id']}")
    except Exception as e:
        print(f"Error sending email: {e}")



def normalize_phone(phone):
    phone = phone.strip().replace(" ", "").replace("+", "")

    # If already in 254 format
    if phone.startswith("2547") and len(phone) == 12:
        return phone

    # If starts with 07...
    if phone.startswith("07") and len(phone) == 10:
        return "254" + phone[1:]

    # If starts with 7...
    if phone.startswith("7") and len(phone) == 9:
        return "254" + phone
    if phone.startswith("2541") and len(phone) == 10:
        return "254" + phone[2:]
    # if number start with 1 or 01 and has 9 digits, assume it's a local number without country code
    if (phone.startswith("1") or phone.startswith("01")) and (len(phone) == 9 or len(phone) == 10):
        return "254" + phone.lstrip("0")

    raise ValueError("Invalid phone number format")



# veryify agent
def verify_agent(request):
    auth = request.headers.get("Authorization")

    # print("=" * 50)
    # print("Authorization Header:", auth)

    token = ""

    if auth:
        token = auth.replace("Bearer ", "")

    # print("Received Token :", repr(token))
    # print("Expected Token :", repr(os.getenv("AGENT_API_KEY")))
    # print("Match:", token == os.getenv("AGENT_API_KEY"))
    # print("=" * 50)

    return token == os.getenv("AGENT_API_KEY")



# helper function to check if can add staff
def can_add_staff(
    tenant
):

    state = (
        get_subscription_state(
            tenant
        )
    )

    if not state["is_active"]:
        return (
            False,
            "Subscription inactive."
        )

    subscription = state[
        "subscription"
    ]

    plan = subscription.plan

    if not plan.allow_staff_accounts:
        return (
            False,
            "Your plan does not include staff accounts."
        )

    current_users = (
        User.objects
        .filter(
            tenant=tenant
        )
        .count()
    )

    if (
        plan.max_users
        and current_users
        >= plan.max_users
    ):
        return (
            False,
            "Your plan's user limit has been reached."
        )

    return True, None

