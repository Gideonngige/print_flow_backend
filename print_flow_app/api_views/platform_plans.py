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

def parse_boolean(value, default=False):
    """
    Safely convert request values to boolean.

    Prevents:
        bool("false") == True
    """

    if isinstance(value, bool):
        return value

    if value is None:
        return default

    if isinstance(value, str):
        value = value.strip().lower()

        if value in [
            "true",
            "1",
            "yes",
            "on",
        ]:
            return True

        if value in [
            "false",
            "0",
            "no",
            "off",
        ]:
            return False

    return bool(value)


# ============================================================
# SERIALIZE PLAN
# ============================================================

def serialize_plan(
    plan,
    include_stats=True
):
    data = {
        "id":
            plan.id,

        "name":
            plan.name,

        "slug":
            plan.slug,

        "description":
            plan.description,

        "monthly_price":
            plan.monthly_price,

        "yearly_price":
            plan.yearly_price,

        "max_users":
            plan.max_users,

        "max_documents":
            plan.max_documents,

        "max_print_jobs":
            plan.max_print_jobs,

        "max_storage_mb":
            plan.max_storage_mb,

        "allow_color_printing":
            plan.allow_color_printing,

        "allow_double_sided":
            plan.allow_double_sided,

        "allow_multiple_printers":
            plan.allow_multiple_printers,

        "allow_staff_accounts":
            plan.allow_staff_accounts,

        "allow_custom_domain":
            plan.allow_custom_domain,

        "advanced_reports":
            plan.advanced_reports,

        "api_access":
            plan.api_access,

        "priority_support":
            plan.priority_support,

        "is_active":
            plan.is_active,

        "is_popular":
            plan.is_popular,

        "created_at":
            plan.created_at,

        "updated_at":
            plan.updated_at,
    }

    if include_stats:

        subscriptions_count = (
            Subscription.objects
            .filter(
                plan=plan
            )
            .count()
        )

        active_subscriptions = (
            Subscription.objects
            .filter(
                plan=plan,
                status="active"
            )
            .count()
        )

        trial_subscriptions = (
            Subscription.objects
            .filter(
                plan=plan,
                status="trial"
            )
            .count()
        )

        data["stats"] = {
            "subscriptions":
                subscriptions_count,

            "active_subscriptions":
                active_subscriptions,

            "trial_subscriptions":
                trial_subscriptions,
        }

    return data


# ============================================================
# GET ALL PLANS / CREATE PLAN
# ============================================================

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def platform_plans(request):

    error_response = (
        ensure_platform_admin(
            request
        )
    )

    if error_response:
        return error_response

    # ========================================================
    # GET ALL PLANS
    # ========================================================

    if request.method == "GET":

        try:
            plans = (
                Plan.objects
                .all()
                .order_by(
                    "monthly_price",
                    "name"
                )
            )

            plans_data = [
                serialize_plan(
                    plan
                )
                for plan in plans
            ]

            return Response({
                "success": True,

                "count":
                    len(plans_data),

                "plans":
                    plans_data,
            })

        except Exception as error:

            print(
                "PLATFORM PLANS ERROR:",
                error
            )

            return Response({
                "success": False,
                "message":
                    "Unable to load subscription plans."
            }, status=500)

    # ========================================================
    # CREATE PLAN
    # ========================================================

    data = request.data

    name = (
        str(
            data.get(
                "name",
                ""
            )
        )
        .strip()
    )

    slug = (
        str(
            data.get(
                "slug",
                ""
            )
        )
        .strip()
        .lower()
    )

    description = (
        str(
            data.get(
                "description",
                ""
            )
        )
        .strip()
    )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    if not name:

        return Response({
            "success": False,
            "message":
                "Plan name is required."
        }, status=400)

    if not slug:
        slug = slugify(
            name
        )

    if (
        Plan.objects
        .filter(
            name__iexact=name
        )
        .exists()
    ):
        return Response({
            "success": False,
            "message":
                "A plan with this name already exists."
        }, status=400)

    if (
        Plan.objects
        .filter(
            slug=slug
        )
        .exists()
    ):
        return Response({
            "success": False,
            "message":
                "A plan with this slug already exists."
        }, status=400)

    # --------------------------------------------------------
    # Numeric fields
    # --------------------------------------------------------

    try:

        monthly_price = Decimal(
            str(
                data.get(
                    "monthly_price",
                    "0.00"
                )
            )
        )

        yearly_price = Decimal(
            str(
                data.get(
                    "yearly_price",
                    "0.00"
                )
            )
        )

        max_users = int(
            data.get(
                "max_users",
                1
            )
        )

        max_documents = int(
            data.get(
                "max_documents",
                100
            )
        )

        max_print_jobs = int(
            data.get(
                "max_print_jobs",
                100
            )
        )

        max_storage_mb = int(
            data.get(
                "max_storage_mb",
                500
            )
        )

    except (
        ValueError,
        TypeError,
        ArithmeticError,
        InvalidOperation,
    ):

        return Response({
            "success": False,
            "message":
                "One or more numeric values are invalid."
        }, status=400)

    # --------------------------------------------------------
    # Numeric validation
    # --------------------------------------------------------

    if monthly_price < 0:

        return Response({
            "success": False,
            "message":
                "Monthly price cannot be negative."
        }, status=400)

    if yearly_price < 0:

        return Response({
            "success": False,
            "message":
                "Yearly price cannot be negative."
        }, status=400)

    if max_users < 1:

        return Response({
            "success": False,
            "message":
                "Maximum users must be at least 1."
        }, status=400)

    if max_documents < 1:

        return Response({
            "success": False,
            "message":
                "Maximum documents must be at least 1."
        }, status=400)

    if max_print_jobs < 1:

        return Response({
            "success": False,
            "message":
                "Maximum print jobs must be at least 1."
        }, status=400)

    if max_storage_mb < 1:

        return Response({
            "success": False,
            "message":
                "Maximum storage must be at least 1 MB."
        }, status=400)

    # --------------------------------------------------------
    # Popular plan
    # --------------------------------------------------------

    is_popular = parse_boolean(
        data.get(
            "is_popular"
        ),
        False
    )

    if is_popular:

        Plan.objects.filter(
            is_popular=True
        ).update(
            is_popular=False
        )

    # --------------------------------------------------------
    # Create
    # --------------------------------------------------------

    try:

        plan = Plan.objects.create(

            name=name,

            slug=slug,

            description=description,

            monthly_price=
                monthly_price,

            yearly_price=
                yearly_price,

            max_users=
                max_users,

            max_documents=
                max_documents,

            max_print_jobs=
                max_print_jobs,

            max_storage_mb=
                max_storage_mb,

            allow_color_printing=
                parse_boolean(
                    data.get(
                        "allow_color_printing"
                    ),
                    True
                ),

            allow_double_sided=
                parse_boolean(
                    data.get(
                        "allow_double_sided"
                    ),
                    True
                ),

            allow_multiple_printers=
                parse_boolean(
                    data.get(
                        "allow_multiple_printers"
                    ),
                    False
                ),

            allow_staff_accounts=
                parse_boolean(
                    data.get(
                        "allow_staff_accounts"
                    ),
                    False
                ),

            allow_custom_domain=
                parse_boolean(
                    data.get(
                        "allow_custom_domain"
                    ),
                    False
                ),

            advanced_reports=
                parse_boolean(
                    data.get(
                        "advanced_reports"
                    ),
                    False
                ),

            api_access=
                parse_boolean(
                    data.get(
                        "api_access"
                    ),
                    False
                ),

            priority_support=
                parse_boolean(
                    data.get(
                        "priority_support"
                    ),
                    False
                ),

            is_active=
                parse_boolean(
                    data.get(
                        "is_active"
                    ),
                    True
                ),

            is_popular=
                is_popular,
        )

        return Response({
            "success": True,

            "message":
                "Plan created successfully.",

            "plan":
                serialize_plan(
                    plan
                ),

        }, status=201)

    except Exception as error:

        print(
            "CREATE PLATFORM PLAN ERROR:",
            error
        )

        return Response({
            "success": False,
            "message":
                "Unable to create subscription plan."
        }, status=500)


# ============================================================
# GET / UPDATE / DELETE PLAN
# ============================================================

@api_view([
    "GET",
    "PATCH",
    "DELETE"
])
@permission_classes([IsAuthenticated])
def platform_plan_detail(
    request,
    plan_id
):

    error_response = (
        ensure_platform_admin(
            request
        )
    )

    if error_response:
        return error_response

    plan = (
        Plan.objects
        .filter(
            id=plan_id
        )
        .first()
    )

    if not plan:

        return Response({
            "success": False,
            "message":
                "Plan not found."
        }, status=404)

    # ========================================================
    # GET PLAN
    # ========================================================

    if request.method == "GET":

        return Response({
            "success": True,

            "plan":
                serialize_plan(
                    plan
                ),
        })

    # ========================================================
    # DELETE PLAN
    # ========================================================

    if request.method == "DELETE":

        subscriptions_exist = (
            Subscription.objects
            .filter(
                plan=plan
            )
            .exists()
        )

        if subscriptions_exist:

            return Response({
                "success": False,

                "message":
                    (
                        "This plan cannot be deleted because "
                        "business subscriptions are using it. "
                        "Deactivate the plan instead."
                    ),
            }, status=400)

        plan_name = (
            plan.name
        )

        plan.delete()

        return Response({
            "success": True,

            "message":
                f"{plan_name} plan deleted successfully."
        })

    # ========================================================
    # UPDATE PLAN
    # ========================================================

    data = request.data

    # --------------------------------------------------------
    # Name
    # --------------------------------------------------------

    if "name" in data:

        name = (
            str(
                data.get(
                    "name",
                    ""
                )
            )
            .strip()
        )

        if not name:

            return Response({
                "success": False,
                "message":
                    "Plan name is required."
            }, status=400)

        duplicate_name = (
            Plan.objects
            .filter(
                name__iexact=name
            )
            .exclude(
                id=plan.id
            )
            .exists()
        )

        if duplicate_name:

            return Response({
                "success": False,
                "message":
                    "Another plan already uses this name."
            }, status=400)

        plan.name = (
            name
        )

    # --------------------------------------------------------
    # Slug
    # --------------------------------------------------------

    if "slug" in data:

        slug = (
            str(
                data.get(
                    "slug",
                    ""
                )
            )
            .strip()
            .lower()
        )

        if not slug:

            slug = slugify(
                plan.name
            )

        duplicate_slug = (
            Plan.objects
            .filter(
                slug=slug
            )
            .exclude(
                id=plan.id
            )
            .exists()
        )

        if duplicate_slug:

            return Response({
                "success": False,
                "message":
                    "Another plan already uses this slug."
            }, status=400)

        plan.slug = (
            slug
        )

    # --------------------------------------------------------
    # Description
    # --------------------------------------------------------

    if "description" in data:

        plan.description = (
            str(
                data.get(
                    "description",
                    ""
                )
            )
            .strip()
        )

    # --------------------------------------------------------
    # Monthly price
    # --------------------------------------------------------

    try:

        if "monthly_price" in data:

            monthly_price = Decimal(
                str(
                    data.get(
                        "monthly_price"
                    )
                )
            )

            if monthly_price < 0:

                return Response({
                    "success": False,
                    "message":
                        "Monthly price cannot be negative."
                }, status=400)

            plan.monthly_price = (
                monthly_price
            )

        # ----------------------------------------------------
        # Yearly price
        # ----------------------------------------------------

        if "yearly_price" in data:

            yearly_price = Decimal(
                str(
                    data.get(
                        "yearly_price"
                    )
                )
            )

            if yearly_price < 0:

                return Response({
                    "success": False,
                    "message":
                        "Yearly price cannot be negative."
                }, status=400)

            plan.yearly_price = (
                yearly_price
            )

        # ----------------------------------------------------
        # Limits
        # ----------------------------------------------------

        if "max_users" in data:

            max_users = int(
                data.get(
                    "max_users"
                )
            )

            if max_users < 1:
                raise ValueError

            plan.max_users = (
                max_users
            )

        if "max_documents" in data:

            max_documents = int(
                data.get(
                    "max_documents"
                )
            )

            if max_documents < 1:
                raise ValueError

            plan.max_documents = (
                max_documents
            )

        if "max_print_jobs" in data:

            max_print_jobs = int(
                data.get(
                    "max_print_jobs"
                )
            )

            if max_print_jobs < 1:
                raise ValueError

            plan.max_print_jobs = (
                max_print_jobs
            )

        if "max_storage_mb" in data:

            max_storage_mb = int(
                data.get(
                    "max_storage_mb"
                )
            )

            if max_storage_mb < 1:
                raise ValueError

            plan.max_storage_mb = (
                max_storage_mb
            )

    except (
        ValueError,
        TypeError,
        ArithmeticError,
        InvalidOperation,
    ):

        return Response({
            "success": False,
            "message":
                "One or more numeric values are invalid."
        }, status=400)

    # --------------------------------------------------------
    # Boolean feature fields
    # --------------------------------------------------------

    boolean_fields = [
        "allow_color_printing",
        "allow_double_sided",
        "allow_multiple_printers",
        "allow_staff_accounts",
        "allow_custom_domain",
        "advanced_reports",
        "api_access",
        "priority_support",
        "is_active",
    ]

    for field in boolean_fields:

        if field in data:

            setattr(
                plan,
                field,
                parse_boolean(
                    data[field],
                    getattr(
                        plan,
                        field
                    )
                )
            )

    # --------------------------------------------------------
    # Popular
    # --------------------------------------------------------

    if "is_popular" in data:

        is_popular = (
            parse_boolean(
                data.get(
                    "is_popular"
                ),
                plan.is_popular
            )
        )

        if is_popular:

            Plan.objects.filter(
                is_popular=True
            ).exclude(
                id=plan.id
            ).update(
                is_popular=False
            )

        plan.is_popular = (
            is_popular
        )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    try:

        plan.save()

        return Response({
            "success": True,

            "message":
                "Plan updated successfully.",

            "plan":
                serialize_plan(
                    plan
                ),
        })

    except Exception as error:

        print(
            "UPDATE PLATFORM PLAN ERROR:",
            error
        )

        return Response({
            "success": False,
            "message":
                "Unable to update subscription plan."
        }, status=500)