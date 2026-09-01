from .common_imports import *


# ============================================================
# LIST + CREATE STAFF
# ============================================================

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def business_staff(request):
    user = request.user

    if user.role not in [
        "business_admin",
        "staff",
    ]:
        return Response({
            "message":
                "You are not allowed to access staff accounts."
        }, status=403)

    tenant = user.tenant

    if not tenant:
        return Response({
            "message":
                "Your account is not linked to a business."
        }, status=400)

    # ========================================================
    # GET
    # ========================================================

    if request.method == "GET":

        search = (
            request.GET.get(
                "search",
                ""
            )
            .strip()
        )

        staff_members = User.objects.filter(
            tenant=tenant,
            role="staff"
        )

        if search:
            staff_members = (
                staff_members.filter(
                    Q(
                        full_name__icontains=
                            search
                    )
                    |
                    Q(
                        email__icontains=
                            search
                    )
                    |
                    Q(
                        phone_number__icontains=
                            search
                    )
                )
            )

        staff_members = staff_members.order_by(
            "-date_joined"
        )

        staff_data = []

        for member in staff_members:

            staff_data.append({
                "id":
                    member.id,

                "full_name":
                    member.full_name,

                "email":
                    member.email,

                "phone_number":
                    member.phone_number,

                "role":
                    member.role,

                "email_verified":
                    member.email_verified,

                "phone_verified":
                    member.phone_verified,

                "is_active":
                    member.is_active,

                "date_joined":
                    member.date_joined,
            })

        subscription = (
            Subscription.objects
            .select_related("plan")
            .filter(
                tenant=tenant
            )
            .first()
        )

        current_users = User.objects.filter(
            tenant=tenant
        ).count()

        limit = (
            subscription.plan.max_users
            if subscription
            else 0
        )

        allow_staff = (
            subscription.plan.allow_staff_accounts
            if subscription
            else False
        )

        return Response({
            "success": True,

            "staff": staff_data,

            "stats": {
                "total_staff":
                    len(staff_data),

                "active_staff":
                    sum(
                        1
                        for member in staff_data
                        if member["is_active"]
                    ),

                "inactive_staff":
                    sum(
                        1
                        for member in staff_data
                        if not member["is_active"]
                    ),

                "total_users":
                    current_users,

                "max_users":
                    limit,

                "allow_staff_accounts":
                    allow_staff,
            }
        })

    # ========================================================
    # POST
    # ========================================================

    if user.role != "business_admin":

        return Response({
            "message":
                "Only the business administrator "
                "can add staff members."
        }, status=403)

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
                "Your business does not have "
                "an active subscription."
        }, status=400)

    plan = subscription.plan

    if not plan.allow_staff_accounts:

        return Response({
            "message":
                "Your current plan does not "
                "support staff accounts."
        }, status=403)

    current_users = User.objects.filter(
        tenant=tenant
    ).count()

    if current_users >= plan.max_users:

        return Response({
            "message":
                f"Your {plan.name} plan allows "
                f"a maximum of {plan.max_users} users."
        }, status=403)

    full_name = (
        request.data
        .get("full_name", "")
        .strip()
    )

    email = (
        request.data
        .get("email", "")
        .strip()
        .lower()
    )

    phone_number = (
        request.data
        .get("phone_number", "")
        .strip()
    )

    password = request.data.get(
        "password"
    )

    if not all([
        full_name,
        email,
        phone_number,
        password,
    ]):

        return Response({
            "message":
                "Full name, email, phone number "
                "and password are required."
        }, status=400)

    if User.objects.filter(
        email__iexact=email
    ).exists():

        return Response({
            "message":
                "A user with this email already exists."
        }, status=400)

    if User.objects.filter(
        phone_number=phone_number
    ).exists():

        return Response({
            "message":
                "A user with this phone number already exists."
        }, status=400)

    if len(password) < 8:

        return Response({
            "message":
                "Password must be at least "
                "8 characters."
        }, status=400)

    staff_member = User.objects.create_user(
        username=email,
        email=email,
        password=password,

        full_name=full_name,
        phone_number=phone_number,

        tenant=tenant,
        role="staff",

        email_verified=True,
        phone_verified=False,

        is_active=True,
    )

    return Response({
        "success": True,

        "message":
            "Staff account created successfully.",

        "staff": {
            "id":
                staff_member.id,

            "full_name":
                staff_member.full_name,

            "email":
                staff_member.email,

            "phone_number":
                staff_member.phone_number,

            "role":
                staff_member.role,

            "is_active":
                staff_member.is_active,

            "date_joined":
                staff_member.date_joined,
        }
    }, status=201)


# ============================================================
# STAFF DETAIL
# ============================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def business_staff_detail(
    request,
    staff_id
):
    user = request.user

    if user.role not in [
        "business_admin",
        "staff",
    ]:
        return Response({
            "message":
                "You are not allowed to access this staff member."
        }, status=403)

    tenant = user.tenant

    staff_member = User.objects.filter(
        id=staff_id,
        tenant=tenant,
        role="staff"
    ).first()

    if not staff_member:

        return Response({
            "message":
                "Staff member not found."
        }, status=404)

    return Response({
        "success": True,

        "staff": {
            "id":
                staff_member.id,

            "full_name":
                staff_member.full_name,

            "email":
                staff_member.email,

            "phone_number":
                staff_member.phone_number,

            "email_verified":
                staff_member.email_verified,

            "phone_verified":
                staff_member.phone_verified,

            "is_active":
                staff_member.is_active,

            "date_joined":
                staff_member.date_joined,
        }
    })


# ============================================================
# UPDATE STAFF
# ============================================================

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_business_staff(
    request,
    staff_id
):
    user = request.user

    if user.role != "business_admin":

        return Response({
            "message":
                "Only the business administrator "
                "can update staff accounts."
        }, status=403)

    tenant = user.tenant

    staff_member = User.objects.filter(
        id=staff_id,
        tenant=tenant,
        role="staff"
    ).first()

    if not staff_member:

        return Response({
            "message":
                "Staff member not found."
        }, status=404)

    full_name = request.data.get(
        "full_name",
        staff_member.full_name
    )

    email = request.data.get(
        "email",
        staff_member.email
    )

    phone_number = request.data.get(
        "phone_number",
        staff_member.phone_number
    )

    email = email.strip().lower()
    full_name = full_name.strip()
    phone_number = phone_number.strip()

    email_exists = (
        User.objects
        .filter(
            email__iexact=email
        )
        .exclude(
            id=staff_member.id
        )
        .exists()
    )

    if email_exists:

        return Response({
            "message":
                "Another user already uses this email."
        }, status=400)

    phone_exists = (
        User.objects
        .filter(
            phone_number=phone_number
        )
        .exclude(
            id=staff_member.id
        )
        .exists()
    )

    if phone_exists:

        return Response({
            "message":
                "Another user already uses "
                "this phone number."
        }, status=400)

    staff_member.full_name = full_name
    staff_member.email = email
    staff_member.username = email
    staff_member.phone_number = phone_number

    staff_member.save(
        update_fields=[
            "full_name",
            "email",
            "username",
            "phone_number",
        ]
    )

    return Response({
        "success": True,

        "message":
            "Staff account updated successfully.",

        "staff": {
            "id":
                staff_member.id,

            "full_name":
                staff_member.full_name,

            "email":
                staff_member.email,

            "phone_number":
                staff_member.phone_number,

            "is_active":
                staff_member.is_active,
        }
    })


# ============================================================
# ACTIVATE / DEACTIVATE STAFF
# ============================================================

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_staff_status(
    request,
    staff_id
):
    user = request.user

    if user.role != "business_admin":

        return Response({
            "message":
                "Only the business administrator "
                "can change staff status."
        }, status=403)

    tenant = user.tenant

    staff_member = User.objects.filter(
        id=staff_id,
        tenant=tenant,
        role="staff"
    ).first()

    if not staff_member:

        return Response({
            "message":
                "Staff member not found."
        }, status=404)

    is_active = request.data.get(
        "is_active"
    )

    if not isinstance(
        is_active,
        bool
    ):

        return Response({
            "message":
                "is_active must be true or false."
        }, status=400)

    staff_member.is_active = is_active

    staff_member.save(
        update_fields=[
            "is_active"
        ]
    )

    return Response({
        "success": True,

        "message":
            "Staff status updated successfully.",

        "staff": {
            "id":
                staff_member.id,

            "is_active":
                staff_member.is_active,
        }
    })


# ============================================================
# RESET STAFF PASSWORD
# ============================================================

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def reset_staff_password(
    request,
    staff_id
):
    user = request.user

    if user.role != "business_admin":

        return Response({
            "message":
                "Only the business administrator "
                "can reset staff passwords."
        }, status=403)

    tenant = user.tenant

    staff_member = User.objects.filter(
        id=staff_id,
        tenant=tenant,
        role="staff"
    ).first()

    if not staff_member:

        return Response({
            "message":
                "Staff member not found."
        }, status=404)

    new_password = request.data.get(
        "password"
    )

    if not new_password:

        return Response({
            "message":
                "New password is required."
        }, status=400)

    if len(new_password) < 8:

        return Response({
            "message":
                "Password must be at least 8 characters."
        }, status=400)

    staff_member.set_password(
        new_password
    )

    staff_member.save(
        update_fields=[
            "password"
        ]
    )

    return Response({
        "success": True,

        "message":
            "Staff password updated successfully."
    })


# ============================================================
# DELETE STAFF
# ============================================================

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_business_staff(
    request,
    staff_id
):
    user = request.user

    if user.role != "business_admin":

        return Response({
            "message":
                "Only the business administrator "
                "can delete staff accounts."
        }, status=403)

    tenant = user.tenant

    staff_member = User.objects.filter(
        id=staff_id,
        tenant=tenant,
        role="staff"
    ).first()

    if not staff_member:

        return Response({
            "message":
                "Staff member not found."
        }, status=404)

    staff_member.delete()

    return Response({
        "success": True,

        "message":
            "Staff account deleted successfully."
    })