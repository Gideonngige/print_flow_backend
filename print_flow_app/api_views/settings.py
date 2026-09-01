from .common_imports import *


# ============================================================
# BUSINESS SETTINGS
# ============================================================

@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def business_settings(request):
    user = request.user

    if user.role not in [
        "business_admin",
        "staff",
    ]:
        return Response({
            "message":
                "You are not allowed to access business settings."
        }, status=403)

    tenant = user.tenant

    if not tenant:
        return Response({
            "message":
                "Your account is not linked to a business."
        }, status=400)

    # --------------------------------------------------------
    # GET
    # --------------------------------------------------------

    if request.method == "GET":
        daraja = (
            DarajaConfiguration.objects
            .filter(
                tenant=tenant
            )
            .first()
        )

        return Response({
            "success": True,

            "business": {
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

                "address":
                    tenant.address,

                "logo":
                    tenant.logo,

                "custom_domain":
                    tenant.custom_domain,

                "is_active":
                    tenant.is_active,
            },

            "daraja": {
                "configured":
                    bool(daraja),

                "environment":
                    daraja.environment
                    if daraja
                    else "sandbox",

                "short_code":
                    daraja.short_code
                    if daraja
                    else "",

                "consumer_key_masked":
                    mask_secret(
                        daraja.consumer_key
                    )
                    if daraja
                    else "",

                "consumer_secret_masked":
                    mask_secret(
                        daraja.consumer_secret
                    )
                    if daraja
                    else "",

                "passkey_masked":
                    mask_secret(
                        daraja.passkey
                    )
                    if daraja
                    else "",

                "callback_url":
                    daraja.callback_url
                    if daraja
                    else "",

                "is_active":
                    daraja.is_active
                    if daraja
                    else False,
            }
        })

    # --------------------------------------------------------
    # PATCH
    # --------------------------------------------------------

    if user.role != "business_admin":
        return Response({
            "message":
                "Only the business administrator "
                "can update business settings."
        }, status=403)

    name = request.data.get(
        "name",
        tenant.name
    )

    email = request.data.get(
        "email",
        tenant.email
    )

    phone_number = request.data.get(
        "phone_number",
        tenant.phone_number
    )

    address = request.data.get(
        "address",
        tenant.address
    )

    logo = request.data.get(
        "logo",
        tenant.logo
    )

    custom_domain = request.data.get(
        "custom_domain",
        tenant.custom_domain
    )

    name = (
        name.strip()
        if isinstance(name, str)
        else tenant.name
    )

    email = (
        email.strip().lower()
        if isinstance(email, str)
        else tenant.email
    )

    phone_number = (
        phone_number.strip()
        if isinstance(
            phone_number,
            str
        )
        else tenant.phone_number
    )

    address = (
        address.strip()
        if isinstance(address, str)
        else tenant.address
    )

    custom_domain = (
        custom_domain.strip()
        if isinstance(
            custom_domain,
            str
        )
        else custom_domain
    )

    if not name:
        return Response({
            "message":
                "Business name is required."
        }, status=400)

    if not email:
        return Response({
            "message":
                "Business email is required."
        }, status=400)

    tenant.name = name
    tenant.email = email
    tenant.phone_number = phone_number
    tenant.address = address
    tenant.logo = logo
    tenant.custom_domain = (
        custom_domain or None
    )

    tenant.save()

    return Response({
        "success": True,

        "message":
            "Business settings updated successfully.",

        "business": {
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

            "address":
                tenant.address,

            "logo":
                tenant.logo,

            "custom_domain":
                tenant.custom_domain,
        }
    })


# ============================================================
# DARAJA SETTINGS
# ============================================================

@api_view(["POST", "PATCH"])
@permission_classes([IsAuthenticated])
def business_daraja_settings(request):
    user = request.user

    if user.role != "business_admin":
        return Response({
            "message":
                "Only the business administrator "
                "can configure M-Pesa."
        }, status=403)

    tenant = user.tenant

    if not tenant:
        return Response({
            "message":
                "Your account is not linked to a business."
        }, status=400)

    daraja = (
        DarajaConfiguration.objects
        .filter(
            tenant=tenant
        )
        .first()
    )

    environment = request.data.get(
        "environment",
        daraja.environment
        if daraja
        else "sandbox"
    )

    short_code = request.data.get(
        "short_code",
        daraja.short_code
        if daraja
        else ""
    )

    consumer_key = request.data.get(
        "consumer_key"
    )

    consumer_secret = request.data.get(
        "consumer_secret"
    )

    passkey = request.data.get(
        "passkey"
    )

    callback_url = request.data.get(
        "callback_url",
        daraja.callback_url
        if daraja
        else ""
    )

    is_active = request.data.get(
        "is_active",
        daraja.is_active
        if daraja
        else True
    )

    if environment not in [
        "sandbox",
        "production",
    ]:
        return Response({
            "message":
                "Environment must be sandbox or production."
        }, status=400)

    if not short_code:
        return Response({
            "message":
                "M-Pesa shortcode is required."
        }, status=400)

    if not daraja:
        if not all([
            consumer_key,
            consumer_secret,
            passkey,
        ]):
            return Response({
                "message":
                    "Consumer key, consumer secret "
                    "and passkey are required."
            }, status=400)

        daraja = (
            DarajaConfiguration.objects.create(
                tenant=tenant,

                environment=
                    environment,

                short_code=
                    short_code,

                consumer_key=
                    consumer_key,

                consumer_secret=
                    consumer_secret,

                passkey=
                    passkey,

                callback_url=
                    callback_url,

                is_active=
                    is_active,
            )
        )

    else:
        daraja.environment = environment
        daraja.short_code = short_code
        daraja.callback_url = callback_url
        daraja.is_active = is_active

        # Only replace secrets when a new
        # value is actually sent.
        if consumer_key:
            daraja.consumer_key = (
                consumer_key
            )

        if consumer_secret:
            daraja.consumer_secret = (
                consumer_secret
            )

        if passkey:
            daraja.passkey = (
                passkey
            )

        daraja.save()

    return Response({
        "success": True,

        "message":
            "M-Pesa configuration saved successfully.",

        "daraja": {
            "configured": True,

            "environment":
                daraja.environment,

            "short_code":
                daraja.short_code,

            "consumer_key_masked":
                mask_secret(
                    daraja.consumer_key
                ),

            "consumer_secret_masked":
                mask_secret(
                    daraja.consumer_secret
                ),

            "passkey_masked":
                mask_secret(
                    daraja.passkey
                ),

            "callback_url":
                daraja.callback_url,

            "is_active":
                daraja.is_active,
        }
    })


def mask_secret(value):
    if not value:
        return ""

    value = str(value)

    if len(value) <= 8:
        return "*" * len(value)

    return (
        value[:4]
        +
        "*" * (
            len(value) - 8
        )
        +
        value[-4:]
    )