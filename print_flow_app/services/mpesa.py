import base64
from datetime import datetime

import requests

from django.conf import settings
import os


def normalize_mpesa_phone(phone):
    """
    Converts:
    0712345678
    0112345678
    +254712345678
    254712345678

    to:
    254712345678
    """

    phone = str(phone).strip().replace(" ", "")

    if phone.startswith("+"):
        phone = phone[1:]

    if phone.startswith("0"):
        phone = "254" + phone[1:]

    if not phone.startswith("254"):
        raise ValueError(
            "Enter a valid Kenyan M-Pesa phone number."
        )

    if len(phone) != 12:
        raise ValueError(
            "Enter a valid Kenyan M-Pesa phone number."
        )

    return phone


def get_mpesa_base_url():
    if os.environ.get("MPESA_ENVIRONMENT") == "production":
        return "https://api.safaricom.co.ke"

    return "https://sandbox.safaricom.co.ke"


def get_mpesa_access_token():

    url = (
        f"{get_mpesa_base_url()}"
        "/oauth/v1/generate"
        "?grant_type=client_credentials"
    )

    response = requests.get(
        url,
        auth=(
            os.environ.get("MPESA_CONSUMER_KEY"),
            os.environ.get("MPESA_CONSUMER_SECRET"),
        ),
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    return data["access_token"]


def initiate_stk_push(
    phone_number,
    amount,
    account_reference,
    description,
):

    phone = normalize_mpesa_phone(
        phone_number
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d%H%M%S"
    )

    raw_password = (
        f"{os.environ.get('MPESA_SHORTCODE')}"
        f"{os.environ.get('MPESA_PASSKEY')}"
        f"{timestamp}"
    )

    password = base64.b64encode(
        raw_password.encode()
    ).decode()

    token = get_mpesa_access_token()

    url = (
        f"{get_mpesa_base_url()}"
        "/mpesa/stkpush/v1/processrequest"
    )

    payload = {
        "BusinessShortCode":
            os.environ.get("MPESA_SHORTCODE"),

        "Password":
            password,

        "Timestamp":
            timestamp,

        "TransactionType":
            os.environ.get("MPESA_TRANSACTION_TYPE"),

        "Amount":
            int(amount),

        "PartyA":
            phone,

        "PartyB":
            os.environ.get("MPESA_SHORTCODE"),

        "PhoneNumber":
            phone,

        "CallBackURL":
            os.environ.get("MPESA_CALLBACK_URL"),

        "AccountReference":
            str(account_reference)[:12],

        "TransactionDesc":
            str(description)[:30],
    }

    response = requests.post(
        url,
        json=payload,
        headers={
            "Authorization":
                f"Bearer {token}",
            "Content-Type":
                "application/json",
        },
        timeout=30,
    )

    response.raise_for_status()

    return response.json()