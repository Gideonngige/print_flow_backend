from .common_imports import *
from .helper import *

import re
import uuid

from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated

from rest_framework_simplejwt.tokens import RefreshToken

from print_flow_app.models import (
    User,
    Tenant,
    Plan,
    Subscription,
)


# ============================================================
# HELPERS
# ============================================================

RESERVED_SUBDOMAINS = {
    "www",
    "admin",
    "api",
    "app",
    "mail",
    "support",
    "platform",
    "platform-admin",
    "dashboard",
    "login",
    "signin",
    "signup",
    "register",
}


def generate_unique_subdomain(business_name):
    """
    Generate a unique tenant slug/subdomain.

    Example:
    Joe Tech Computers
        -> joe-tech-computers

    If it already exists:
        -> joe-tech-computers-2
    """

    base = slugify(business_name)

    if not base:
        base = "business"

    if base in RESERVED_SUBDOMAINS:
        base = f"{base}-business"

    slug = base
    counter = 2

    while Tenant.objects.filter(
        subdomain=slug
    ).exists():

        slug = f"{base}-{counter}"
        counter += 1

    return slug


def serialize_tenant(tenant):
    if not tenant:
        return None

    return {
        "id": tenant.id,
        "name": tenant.name,
        "slug": tenant.slug,
        "subdomain": tenant.subdomain,
        "email": tenant.email,
        "phone_number": tenant.phone_number,
        "address": tenant.address,
        "logo": tenant.logo,
        "custom_domain": tenant.custom_domain,
        "is_active": tenant.is_active,

        # Change this domain when you deploy your
        # actual PrintFlow domain.
        "portal_url": (
            f"https://{tenant.subdomain}."
            f"printflow.co.ke"
        ),
    }


def serialize_subscription(subscription):
    if not subscription:
        return None

    return {
        "id": subscription.id,
        "status": subscription.status,
        "billing_cycle": subscription.billing_cycle,
        "auto_renew": subscription.auto_renew,

        "start_date": subscription.start_date.isoformat()
        if subscription.start_date
        else None,

        "current_period_start":
            subscription.current_period_start.isoformat()
            if subscription.current_period_start
            else None,

        "current_period_end":
            subscription.current_period_end.isoformat()
            if subscription.current_period_end
            else None,

        "trial_start":
            subscription.trial_start.isoformat()
            if subscription.trial_start
            else None,

        "trial_end":
            subscription.trial_end.isoformat()
            if subscription.trial_end
            else None,

        "plan": {
            "id": subscription.plan.id,
            "name": subscription.plan.name,
            "slug": subscription.plan.slug,

            "monthly_price":
                str(subscription.plan.monthly_price),

            "yearly_price":
                str(subscription.plan.yearly_price),

            "max_users":
                subscription.plan.max_users,

            "max_documents":
                subscription.plan.max_documents,

            "max_print_jobs":
                subscription.plan.max_print_jobs,

            "max_storage_mb":
                subscription.plan.max_storage_mb,
        }
    }


def serialize_user(user):
    return {
        "id": user.id,
        "user_id": user.id,
        "full_name": user.full_name,
        "user_name": user.full_name,
        "email": user.email,
        "user_email": user.email,
        "phone_number": user.phone_number,
        "role": user.role,
        "phone_verified": user.phone_verified,
        "email_verified": user.email_verified,
        "date_joined": user.date_joined.isoformat(),
    }


# ============================================================
# TEST EMAIL
# ============================================================

@api_view(["POST"])
@permission_classes([AllowAny])
def send_test_email(request):

    to_email = request.data.get("email")

    if not to_email:
        return JsonResponse({
            "message": "Email is required."
        }, status=400)

    subject = "Test Email from PrintFlow"

    html = """
        <h1>PrintFlow Email Test</h1>

        <p>
            If you received this email,
            your email configuration is working.
        </p>
    """

    try:

        send_email(
            to_email,
            subject,
            html
        )

        return JsonResponse({
            "message":
                "Test email sent successfully."
        })

    except Exception as e:

        return JsonResponse({
            "message":
                "Failed to send test email.",
            "error": str(e)
        }, status=500)


# ============================================================
# BUSINESS REGISTRATION
# ============================================================

@api_view(["POST"])
@permission_classes([AllowAny])
def register_business(request):
    """
    Creates:

    Tenant
      ↓
    Business Admin User
      ↓
    Subscription
      ↓
    Verification Email
    """

    try:

        data = request.data

        business_name = (
            data.get("business_name", "")
            .strip()
        )

        full_name = (
            data.get("full_name", "")
            .strip()
        )

        email = (
            data.get("email", "")
            .strip()
            .lower()
        )

        phone_number = (
            data.get("phone_number", "")
            .strip()
        )

        address = (
            data.get("address", "")
            .strip()
        )

        password = data.get("password")

        plan_id = data.get("plan_id")

        billing_cycle = data.get(
            "billing_cycle",
            "monthly"
        )


        # ----------------------------------------------------
        # Required fields
        # ----------------------------------------------------

        if not all([
            business_name,
            full_name,
            email,
            phone_number,
            password,
        ]):

            return JsonResponse({
                "message":
                    "Business name, full name, email, "
                    "phone number and password are required."
            }, status=400)


        # ----------------------------------------------------
        # Billing cycle
        # ----------------------------------------------------

        if billing_cycle not in [
            "monthly",
            "yearly",
        ]:

            return JsonResponse({
                "message":
                    "Billing cycle must be monthly or yearly."
            }, status=400)


        # ----------------------------------------------------
        # Kenyan phone validation
        # ----------------------------------------------------

        phone_pattern = (
            r"^(\+254|254|0)[17]\d{8}$"
        )

        if not re.match(
            phone_pattern,
            phone_number
        ):

            return JsonResponse({
                "message":
                    "Enter a valid Kenyan phone number."
            }, status=400)


        # ----------------------------------------------------
        # User uniqueness
        # ----------------------------------------------------

        if User.objects.filter(
            email__iexact=email
        ).exists():

            return JsonResponse({
                "message":
                    "An account with this email already exists."
            }, status=400)


        if User.objects.filter(
            phone_number=phone_number
        ).exists():

            return JsonResponse({
                "message":
                    "An account with this phone number already exists."
            }, status=400)


        # ----------------------------------------------------
        # Password validation
        # ----------------------------------------------------

        try:

            validate_password(password)

        except ValidationError as error:

            return JsonResponse({
                "message": "Invalid password.",
                "errors": list(error.messages),
            }, status=400)


        # ----------------------------------------------------
        # Plan
        # ----------------------------------------------------

        if plan_id:

            plan = Plan.objects.filter(
                id=plan_id,
                is_active=True
            ).first()

        else:

            # Default SaaS plan when user did not
            # arrive from Pricing page.
            plan = Plan.objects.filter(
                slug="starter",
                is_active=True
            ).first()


        if not plan:

            return JsonResponse({
                "message":
                    "The selected subscription plan "
                    "is not available."
            }, status=400)


        now = timezone.now()

        # 14-day SaaS trial
        trial_end = (
            now +
            timedelta(days=14)
        )


        # ----------------------------------------------------
        # Create SaaS resources atomically
        # ----------------------------------------------------

        with transaction.atomic():

            tenant_slug = (
                generate_unique_subdomain(
                    business_name
                )
            )


            tenant = Tenant.objects.create(
                name=business_name,
                slug=tenant_slug,
                subdomain=tenant_slug,
                email=email,
                phone_number=phone_number,
                address=address,
            )


            verification_token = str(
                uuid.uuid4()
            )


            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                full_name=full_name,
                phone_number=phone_number,

                tenant=tenant,

                # Never trust the frontend
                # to set this role.
                role="business_admin",

                email_verification_token=
                    verification_token,

                email_verified=False,
            )


            subscription = (
                Subscription.objects.create(
                    tenant=tenant,
                    plan=plan,

                    billing_cycle=
                        billing_cycle,

                    status="trial",

                    start_date=now,

                    current_period_start=now,

                    current_period_end=
                        trial_end,

                    trial_start=now,
                    trial_end=trial_end,

                    auto_renew=True,
                )
            )


        # ----------------------------------------------------
        # Verification email
        # ----------------------------------------------------

        verification_link = (
            "https://print-flow-backend-ppm9"
            ".onrender.com/"
            f"verify_email/?token="
            f"{verification_token}"
        )


        email_warning = None

        try:

            send_email(
                email,
                "Verify Your PrintFlow Account",
                f"""
                <div
                    style="
                    font-family: Arial, sans-serif;
                    max-width: 600px;
                    margin: auto;
                    padding: 20px;
                    color: #333;
                    "
                >

                    <h2 style="color:#2563EB;">
                        Welcome to PrintFlow
                    </h2>

                    <p>
                        Hi {full_name},
                    </p>

                    <p>
                        Your PrintFlow business workspace
                        for <strong>{business_name}</strong>
                        has been created successfully.
                    </p>

                    <p>
                        Please verify your email address
                        before signing in.
                    </p>

                    <div
                        style="
                        margin: 30px 0;
                        "
                    >

                        <a
                            href="{verification_link}"
                            style="
                            background-color:#2563EB;
                            color:white;
                            padding:12px 24px;
                            text-decoration:none;
                            border-radius:8px;
                            font-weight:bold;
                            display:inline-block;
                            "
                        >
                            Verify Email
                        </a>

                    </div>

                    <p>
                        Your business portal:
                    </p>

                    <p
                        style="
                        color:#2563EB;
                        font-weight:bold;
                        "
                    >
                        {tenant.subdomain}.printflow.co.ke
                    </p>

                    <p>
                        If the button does not work,
                        copy this link:
                    </p>

                    <p
                        style="
                        word-break:break-all;
                        color:#2563EB;
                        "
                    >
                        {verification_link}
                    </p>

                    <hr
                        style="
                        margin:30px 0;
                        "
                    />

                    <p
                        style="
                        font-size:14px;
                        color:#777;
                        "
                    >
                        PrintFlow Team
                    </p>

                </div>
                """
            )

        except Exception as email_error:

            print(
                "VERIFICATION EMAIL ERROR:",
                email_error
            )

            email_warning = (
                "Business created, but the "
                "verification email could not "
                "be sent."
            )


        return JsonResponse({
            "success": True,

            "message":
                "Business account created successfully. "
                "Please verify your email.",

            "email_warning":
                email_warning,

            "user":
                serialize_user(user),

            "tenant":
                serialize_tenant(tenant),

            "subscription":
                serialize_subscription(
                    subscription
                ),

        }, status=201)


    except Exception as e:

        print(
            "BUSINESS REGISTRATION ERROR:",
            str(e)
        )

        return JsonResponse({
            "success": False,
            "message":
                "Unable to create business account.",
            "error": str(e),
        }, status=500)


# ============================================================
# EMAIL VERIFICATION
# ============================================================

@api_view(["GET"])
@permission_classes([AllowAny])
def verify_email(request):

    token = request.GET.get("token")

    if not token:

        return render(
            request,
            "auth/email_result.html",
            {
                "status": "error",
                "title": "Invalid Request",
                "message":
                    "Verification token is missing."
            }
        )


    user = User.objects.filter(
        email_verification_token=token
    ).first()


    if not user:

        return render(
            request,
            "auth/email_result.html",
            {
                "status": "error",
                "title": "Invalid Token",
                "message":
                    "This verification link "
                    "is invalid."
            }
        )


    if user.email_verified:

        return render(
            request,
            "auth/email_result.html",
            {
                "status": "success",
                "title": "Already Verified",
                "message":
                    "Your email is already verified."
            }
        )


    user.email_verified = True
    user.email_verification_token = None

    user.save(
        update_fields=[
            "email_verified",
            "email_verification_token",
        ]
    )


    return render(
        request,
        "auth/email_result.html",
        {
            "status": "success",
            "title": "Email Verified 🎉",
            "message":
                "Your PrintFlow account has been "
                "verified successfully. "
                "You can now sign in."
        }
    )


# ============================================================
# RESEND VERIFICATION EMAIL
# ============================================================

@api_view(["POST"])
@permission_classes([AllowAny])
def resend_verification_email(request):

    email = (
        request.data
        .get("email", "")
        .strip()
        .lower()
    )


    # Generic response prevents email enumeration.
    generic_message = (
        "If an unverified account exists with "
        "that email, a verification email "
        "has been sent."
    )


    if not email:

        return JsonResponse({
            "message": generic_message
        })


    user = User.objects.filter(
        email__iexact=email
    ).first()


    if (
        not user or
        user.email_verified
    ):

        return JsonResponse({
            "message": generic_message
        })


    token = str(uuid.uuid4())

    user.email_verification_token = token

    user.save(
        update_fields=[
            "email_verification_token"
        ]
    )


    link = (
        "https://print-flow-backend-ppm9"
        ".onrender.com/"
        f"verify_email/?token={token}"
    )


    try:

        send_email(
            user.email,
            "Verify Your PrintFlow Account",
            f"""
            <h2>
                Verify your PrintFlow account
            </h2>

            <p>
                Click below to verify your email.
            </p>

            <a href="{link}">
                Verify Email
            </a>
            """
        )

    except Exception as e:

        print(
            "RESEND VERIFICATION ERROR:",
            e
        )


    return JsonResponse({
        "message": generic_message
    })


# ============================================================
# SIGN IN
# ============================================================

@api_view(["POST"])
@permission_classes([AllowAny])
def signin(request):

    try:

        email = (
            request.data
            .get("email", "")
            .strip()
            .lower()
        )

        password = request.data.get(
            "password"
        )


        if not email or not password:

            return JsonResponse({
                "message":
                    "Email and password are required."
            }, status=400)


        user = authenticate(
            request,
            username=email,
            password=password
        )


        if not user:

            return JsonResponse({
                "message":
                    "Invalid email or password."
            }, status=401)


        if not user.is_active:

            return JsonResponse({
                "message":
                    "This account has been disabled."
            }, status=403)


        if not user.email_verified:

            return JsonResponse({
                "message":
                    "Please verify your email "
                    "before signing in.",
                "email_verification_required":
                    True,
            }, status=403)


        # ----------------------------------------------------
        # Tenant checks
        # ----------------------------------------------------

        tenant = user.tenant

        if (
            user.role != "platform_admin" and
            not tenant
        ):

            return JsonResponse({
                "message":
                    "Your account is not associated "
                    "with a business."
            }, status=403)


        if (
            tenant and
            not tenant.is_active
        ):

            return JsonResponse({
                "message":
                    "This business account is inactive."
            }, status=403)


        # ----------------------------------------------------
        # Subscription
        # ----------------------------------------------------

        subscription = None

        if tenant:

            subscription = (
                Subscription.objects
                .select_related("plan")
                .filter(
                    tenant=tenant
                )
                .first()
            )


            # Automatically expire old subscriptions
            if (
                subscription and
                subscription.current_period_end and
                subscription.current_period_end
                    < timezone.now() and
                subscription.status
                    in ["active", "trial"]
            ):

                subscription.status = "expired"

                subscription.save(
                    update_fields=[
                        "status"
                    ]
                )


        # ----------------------------------------------------
        # JWT
        # ----------------------------------------------------

        refresh = RefreshToken.for_user(
            user
        )


        return JsonResponse({
            "success": True,
            "message": "Login successful.",

            "access_token":
                str(refresh.access_token),

            "refresh_token":
                str(refresh),

            "user":
                serialize_user(user),

            "tenant":
                serialize_tenant(tenant),

            "subscription":
                serialize_subscription(
                    subscription
                ),

        })


    except Exception as e:

        print(
            "SIGNIN ERROR:",
            str(e)
        )

        return JsonResponse({
            "message":
                "Unable to sign in.",
            "error": str(e)
        }, status=500)


# ============================================================
# PASSWORD RESET REQUEST
# ============================================================

@api_view(["POST"])
@permission_classes([AllowAny])
def request_reset(request):

    email = (
        request.data
        .get("email", "")
        .strip()
        .lower()
    )


    generic_message = (
        "If an account exists with that email, "
        "a password reset link has been sent."
    )


    if not email:

        return JsonResponse({
            "message":
                "Email address is required."
        }, status=400)


    user = User.objects.filter(
        email__iexact=email
    ).first()


    # Do not reveal whether user exists.
    if not user:

        return JsonResponse({
            "message":
                generic_message
        })


    token = str(uuid.uuid4())

    user.reset_token = token

    user.save(
        update_fields=[
            "reset_token"
        ]
    )


    link = (
        "https://print-flow-backend-ppm9"
        ".onrender.com/"
        f"reset_password/?token={token}"
    )


    try:

        send_email(
            user.email,
            "Reset Your PrintFlow Password",
            f"""
            <div
                style="
                font-family:Arial,sans-serif;
                max-width:600px;
                margin:auto;
                padding:20px;
                "
            >

                <h2 style="color:#2563EB;">
                    Reset Your PrintFlow Password
                </h2>

                <p>
                    Hi {user.full_name},
                </p>

                <p>
                    We received a request to
                    reset your PrintFlow password.
                </p>

                <div style="margin:30px 0;">

                    <a
                        href="{link}"
                        style="
                        background:#2563EB;
                        color:white;
                        padding:12px 24px;
                        text-decoration:none;
                        border-radius:8px;
                        font-weight:bold;
                        "
                    >
                        Reset Password
                    </a>

                </div>

                <p>
                    If you did not request this,
                    you can ignore this email.
                </p>

                <hr style="margin:30px 0;" />

                <p
                    style="
                    font-size:14px;
                    color:#777;
                    "
                >
                    PrintFlow Team
                </p>

            </div>
            """
        )


    except Exception as e:

        print(
            "RESET EMAIL ERROR:",
            str(e)
        )


    return JsonResponse({
        "message":
            generic_message
    })


# ============================================================
# RESET PASSWORD
# ============================================================

@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def reset_password(request):

    token = (
        request.GET.get("token") or
        request.data.get("token")
    )


    if not token:

        return render(
            request,
            "auth/reset_result.html",
            {
                "status": "error",
                "message":
                    "Missing reset token."
            }
        )


    user = User.objects.filter(
        reset_token=token
    ).first()


    if not user:

        return render(
            request,
            "auth/reset_result.html",
            {
                "status": "error",
                "message":
                    "Invalid reset link."
            }
        )


    # --------------------------------------------------------
    # GET
    # --------------------------------------------------------

    if request.method == "GET":

        return render(
            request,
            "auth/reset_password.html",
            {
                "token": token
            }
        )


    # --------------------------------------------------------
    # POST
    # --------------------------------------------------------

    password = request.data.get(
        "password"
    )

    confirm_password = request.data.get(
        "confirm_password"
    )


    if not password or not confirm_password:

        return render(
            request,
            "auth/reset_password.html",
            {
                "token": token,
                "error":
                    "All fields are required."
            }
        )


    if password != confirm_password:

        return render(
            request,
            "auth/reset_password.html",
            {
                "token": token,
                "error":
                    "Passwords do not match."
            }
        )


    try:

        validate_password(
            password,
            user=user
        )

    except ValidationError as error:

        return render(
            request,
            "auth/reset_password.html",
            {
                "token": token,
                "error":
                    " ".join(error.messages)
            }
        )


    user.set_password(password)

    user.reset_token = None

    user.save(
        update_fields=[
            "password",
            "reset_token",
        ]
    )


    return render(
        request,
        "auth/reset_result.html",
        {
            "status": "success",
            "message":
                "Password updated successfully. "
                "You can now sign in."
        }
    )


# ============================================================
# REFRESH TOKEN
# ============================================================

@api_view(["POST"])
@permission_classes([AllowAny])
def refresh_token(request):

    try:

        token = request.data.get(
            "refresh_token"
        )


        if not token:

            return JsonResponse({
                "message":
                    "Refresh token is required."
            }, status=400)


        refresh = RefreshToken(token)


        return JsonResponse({
            "access_token":
                str(refresh.access_token)
        })


    except Exception:

        return JsonResponse({
            "message":
                "Invalid or expired refresh token."
        }, status=401)


# ============================================================
# DELETE PERSONAL ACCOUNT
# ============================================================

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_account(request):

    try:

        user = request.user


        # Business administrator deletion requires
        # separate tenant/business deletion logic.
        if user.role == "business_admin":

            return JsonResponse({
                "message":
                    "Business administrators cannot "
                    "delete their account directly. "
                    "Delete or transfer the business "
                    "workspace first."
            }, status=400)


        if user.role == "platform_admin":

            return JsonResponse({
                "message":
                    "Platform administrator accounts "
                    "cannot be deleted through this API."
            }, status=400)


        user.delete()


        return JsonResponse({
            "success": True,
            "message":
                "Account deleted successfully."
        })


    except Exception as e:

        return JsonResponse({
            "message":
                "Unable to delete account.",
            "error": str(e)
        }, status=500)


# ============================================================
# AUTH CHECK
# ============================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def auth_check(request):

    user = request.user

    tenant = user.tenant

    subscription = None


    if tenant:

        subscription = (
            Subscription.objects
            .select_related("plan")
            .filter(
                tenant=tenant
            )
            .first()
        )


    return JsonResponse({
        "authenticated": True,

        "user":
            serialize_user(user),

        "tenant":
            serialize_tenant(tenant),

        "subscription":
            serialize_subscription(
                subscription
            ),
    })