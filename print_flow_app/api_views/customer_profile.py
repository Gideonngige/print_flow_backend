from .common_imports import *


# ============================================================
# CUSTOMER PROFILE
# ============================================================

@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def customer_profile(request):

    user = request.user

    if user.role != "customer":
        return Response({
            "success": False,
            "message":
                "Only customer accounts can access this profile."
        }, status=403)

    # ========================================================
    # ACTIVE TENANT
    # ========================================================

    tenant_slug = (
        request.headers
        .get(
            "X-Tenant-Slug",
            ""
        )
        .strip()
    )

    tenant = None
    membership = None

    if tenant_slug:

        tenant = (
            Tenant.objects
            .filter(
                slug=tenant_slug,
                is_active=True
            )
            .first()
        )

        if tenant:

            membership = (
                CustomerTenantMembership.objects
                .filter(
                    customer=user,
                    tenant=tenant
                )
                .first()
            )

    # ========================================================
    # GET
    # ========================================================

    if request.method == "GET":

        return Response({
            "success": True,

            "customer": {
                "id":
                    user.id,

                "username":
                    user.username,

                "full_name":
                    user.full_name,

                "email":
                    user.email,

                "phone_number":
                    user.phone_number,

                "email_verified":
                    user.email_verified,

                "phone_verified":
                    user.phone_verified,

                "date_joined":
                    user.date_joined,
            },

            "current_business": {
                "id":
                    tenant.id,

                "name":
                    tenant.name,

                "slug":
                    tenant.slug,

                "subdomain":
                    tenant.subdomain,

                "logo":
                    tenant.logo,

                "email":
                    tenant.email,

                "phone_number":
                    tenant.phone_number,

                "address":
                    tenant.address,

                "membership_status":
                    membership.status
                    if membership
                    else None,

                "joined_at":
                    membership.joined_at
                    if membership
                    else None,
            }
            if tenant
            else None,
        })

    # ========================================================
    # PATCH
    # ========================================================

    full_name = request.data.get(
        "full_name",
        user.full_name
    )

    email = request.data.get(
        "email",
        user.email
    )

    phone_number = request.data.get(
        "phone_number",
        user.phone_number
    )

    full_name = (
        full_name.strip()
        if isinstance(
            full_name,
            str
        )
        else user.full_name
    )

    email = (
        email.strip().lower()
        if isinstance(
            email,
            str
        )
        else user.email
    )

    phone_number = (
        phone_number.strip()
        if isinstance(
            phone_number,
            str
        )
        else user.phone_number
    )

    if not full_name:

        return Response({
            "success": False,
            "message":
                "Full name is required."
        }, status=400)

    if not email:

        return Response({
            "success": False,
            "message":
                "Email address is required."
        }, status=400)

    if not phone_number:

        return Response({
            "success": False,
            "message":
                "Phone number is required."
        }, status=400)

    # ========================================================
    # UNIQUE EMAIL
    # ========================================================

    email_exists = (
        User.objects
        .filter(
            email__iexact=email
        )
        .exclude(
            id=user.id
        )
        .exists()
    )

    if email_exists:

        return Response({
            "success": False,
            "message":
                "Another account already uses this email address."
        }, status=400)

    # ========================================================
    # UNIQUE PHONE
    # ========================================================

    phone_exists = (
        User.objects
        .filter(
            phone_number=phone_number
        )
        .exclude(
            id=user.id
        )
        .exists()
    )

    if phone_exists:

        return Response({
            "success": False,
            "message":
                "Another account already uses this phone number."
        }, status=400)

    # ========================================================
    # EMAIL CHANGED
    # ========================================================

    email_changed = (
        email.lower() !=
        user.email.lower()
    )

    # ========================================================
    # PHONE CHANGED
    # ========================================================

    phone_changed = (
        phone_number !=
        user.phone_number
    )

    user.full_name = (
        full_name
    )

    user.email = (
        email
    )

    user.phone_number = (
        phone_number
    )

    # If you're using email as username
    # keep username in sync.
    user.username = (
        email
    )

    if email_changed:
        user.email_verified = (
            False
        )

    if phone_changed:
        user.phone_verified = (
            False
        )

    user.save(
        update_fields=[
            "full_name",
            "email",
            "username",
            "phone_number",
            "email_verified",
            "phone_verified",
        ]
    )

    return Response({
        "success": True,

        "message":
            "Profile updated successfully.",

        "customer": {
            "id":
                user.id,

            "username":
                user.username,

            "full_name":
                user.full_name,

            "email":
                user.email,

            "phone_number":
                user.phone_number,

            "email_verified":
                user.email_verified,

            "phone_verified":
                user.phone_verified,

            "date_joined":
                user.date_joined,
        }
    })