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
# LIST PLATFORM USERS
# ============================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def platform_users(request):

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

        role_filter = (
            request.query_params
            .get(
                "role",
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

        tenant_id = (
            request.query_params
            .get(
                "tenant",
                ""
            )
            .strip()
        )


        users = (
            User.objects
            .select_related(
                "tenant"
            )
            .all()
            .order_by(
                "-date_joined"
            )
        )


        # ----------------------------------------------------
        # Search
        # ----------------------------------------------------

        if search:
            users = users.filter(
                Q(
                    full_name__icontains=search
                )
                |
                Q(
                    email__icontains=search
                )
                |
                Q(
                    username__icontains=search
                )
                |
                Q(
                    phone_number__icontains=search
                )
            )


        # ----------------------------------------------------
        # Role
        # ----------------------------------------------------

        if role_filter:
            users = users.filter(
                role=role_filter
            )


        # ----------------------------------------------------
        # Status
        # ----------------------------------------------------

        if status_filter == "active":
            users = users.filter(
                is_active=True
            )

        elif status_filter == "inactive":
            users = users.filter(
                is_active=False
            )


        # ----------------------------------------------------
        # Tenant
        # ----------------------------------------------------

        if tenant_id:

            try:
                tenant_id = int(
                    tenant_id
                )

            except (
                ValueError,
                TypeError
            ):
                return Response({
                    "success": False,
                    "message":
                        "Invalid business filter."
                }, status=400)


            users = users.filter(
                tenant_id=tenant_id
            )


        users = users.distinct()


        users_data = []


        for user in users:

            memberships = []

            if user.role == "customer":

                customer_memberships = (
                    CustomerTenantMembership.objects
                    .filter(
                        customer=user
                    )
                    .select_related(
                        "tenant"
                    )
                    .order_by(
                        "-joined_at"
                    )
                )


                for membership in customer_memberships:

                    memberships.append({
                        "id":
                            membership.id,

                        "status":
                            membership.status,

                        "joined_at":
                            membership.joined_at,

                        "tenant": {
                            "id":
                                membership.tenant.id,

                            "name":
                                membership.tenant.name,

                            "slug":
                                membership.tenant.slug,

                            "is_active":
                                membership.tenant.is_active,
                        }
                    })


            users_data.append({
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

                "role":
                    user.role,

                "is_active":
                    user.is_active,

                "is_staff":
                    user.is_staff,

                "is_superuser":
                    user.is_superuser,

                "email_verified":
                    user.email_verified,

                "phone_verified":
                    user.phone_verified,

                "date_joined":
                    user.date_joined,

                "last_login":
                    user.last_login,

                "tenant": {
                    "id":
                        user.tenant.id,

                    "name":
                        user.tenant.name,

                    "slug":
                        user.tenant.slug,

                    "is_active":
                        user.tenant.is_active,
                }
                if user.tenant
                else None,

                "memberships":
                    memberships,
            })


        # ----------------------------------------------------
        # Stats
        # ----------------------------------------------------

        stats = {
            "total":
                User.objects.count(),

            "platform_admins":
                User.objects
                .filter(
                    role="platform_admin"
                )
                .count(),

            "business_admins":
                User.objects
                .filter(
                    role="business_admin"
                )
                .count(),

            "staff":
                User.objects
                .filter(
                    role="staff"
                )
                .count(),

            "customers":
                User.objects
                .filter(
                    role="customer"
                )
                .count(),

            "active":
                User.objects
                .filter(
                    is_active=True
                )
                .count(),

            "inactive":
                User.objects
                .filter(
                    is_active=False
                )
                .count(),
        }


        return Response({
            "success": True,

            "count":
                len(users_data),

            "stats":
                stats,

            "users":
                users_data,
        })


    except Exception as error:

        print(
            "PLATFORM USERS ERROR:",
            error
        )

        return Response({
            "success": False,
            "message":
                "Unable to load platform users."
        }, status=500)


# ============================================================
# USER DETAIL
# ============================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def platform_user_detail(
    request,
    user_id
):

    error_response = ensure_platform_admin(
        request
    )

    if error_response:
        return error_response


    user = (
        User.objects
        .select_related(
            "tenant"
        )
        .filter(
            id=user_id
        )
        .first()
    )


    if not user:
        return Response({
            "success": False,
            "message":
                "User not found."
        }, status=404)


    memberships = []


    if user.role == "customer":

        customer_memberships = (
            CustomerTenantMembership.objects
            .filter(
                customer=user
            )
            .select_related(
                "tenant"
            )
            .order_by(
                "-joined_at"
            )
        )


        for membership in customer_memberships:

            memberships.append({
                "id":
                    membership.id,

                "status":
                    membership.status,

                "joined_at":
                    membership.joined_at,

                "tenant": {
                    "id":
                        membership.tenant.id,

                    "name":
                        membership.tenant.name,

                    "slug":
                        membership.tenant.slug,

                    "email":
                        membership.tenant.email,

                    "is_active":
                        membership.tenant.is_active,
                }
            })


    documents_count = (
        Document.objects
        .filter(
            user=user
        )
        .count()
    )


    print_jobs_count = (
        PrintJob.objects
        .filter(
            user=user
        )
        .count()
    )


    total_customer_payments = (
        Payment.objects
        .filter(
            user=user,
            status="paid"
        )
        .aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )


    return Response({
        "success": True,

        "user": {
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

            "role":
                user.role,

            "is_active":
                user.is_active,

            "is_staff":
                user.is_staff,

            "is_superuser":
                user.is_superuser,

            "email_verified":
                user.email_verified,

            "phone_verified":
                user.phone_verified,

            "date_joined":
                user.date_joined,

            "last_login":
                user.last_login,

            "tenant": {
                "id":
                    user.tenant.id,

                "name":
                    user.tenant.name,

                "slug":
                    user.tenant.slug,
            }
            if user.tenant
            else None,

            "memberships":
                memberships,

            "stats": {
                "documents":
                    documents_count,

                "print_jobs":
                    print_jobs_count,

                "total_spent":
                    total_customer_payments,
            },
        }
    })


# ============================================================
# UPDATE USER STATUS
# ============================================================

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def platform_update_user_status(
    request,
    user_id
):

    error_response = ensure_platform_admin(
        request
    )

    if error_response:
        return error_response


    target_user = (
        User.objects
        .filter(
            id=user_id
        )
        .first()
    )


    if not target_user:
        return Response({
            "success": False,
            "message":
                "User not found."
        }, status=404)


    if target_user.id == request.user.id:

        return Response({
            "success": False,
            "message":
                "You cannot deactivate your own platform administrator account."
        }, status=400)


    if target_user.is_superuser:

        return Response({
            "success": False,
            "message":
                "A superuser account cannot be changed from this endpoint."
        }, status=400)


    is_active = (
        request.data.get(
            "is_active"
        )
    )


    if not isinstance(
        is_active,
        bool
    ):

        return Response({
            "success": False,
            "message":
                "is_active must be true or false."
        }, status=400)


    target_user.is_active = (
        is_active
    )


    target_user.save(
        update_fields=[
            "is_active"
        ]
    )


    return Response({
        "success": True,

        "message":
            (
                "User activated successfully."
                if target_user.is_active
                else "User deactivated successfully."
            ),

        "user": {
            "id":
                target_user.id,

            "is_active":
                target_user.is_active,
        }
    })