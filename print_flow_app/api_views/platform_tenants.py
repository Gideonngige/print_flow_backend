from .common_imports import *


# ============================================================
# PLATFORM ADMIN GUARD HELPER
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
# LIST TENANTS
# ============================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def platform_tenants(request):

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

        subscription_status = (
            request.query_params
            .get(
                "subscription_status",
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

        tenants = (
            Tenant.objects
            .all()
            .order_by(
                "-created_at"
            )
        )

        # ====================================================
        # SEARCH
        # ====================================================

        if search:
            tenants = tenants.filter(
                Q(
                    name__icontains=
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
                |
                Q(
                    slug__icontains=
                        search
                )
                |
                Q(
                    subdomain__icontains=
                        search
                )
            )

        # ====================================================
        # TENANT STATUS
        # ====================================================

        if status_filter == "active":

            tenants = tenants.filter(
                is_active=True
            )

        elif status_filter == "inactive":

            tenants = tenants.filter(
                is_active=False
            )

        # ====================================================
        # SUBSCRIPTION STATUS
        # ====================================================

        if subscription_status:

            tenants = tenants.filter(
                subscription__status=
                    subscription_status
            )

        # ====================================================
        # PLAN FILTER
        # ====================================================

        if plan_slug:

            tenants = tenants.filter(
                subscription__plan__slug=
                    plan_slug
            )

        tenants = (
            tenants.distinct()
        )

        tenants_data = []

        # ====================================================
        # SERIALIZE
        # ====================================================

        for tenant in tenants:

            subscription = (
                Subscription.objects
                .filter(
                    tenant=tenant
                )
                .select_related(
                    "plan"
                )
                .order_by(
                    "-created_at"
                )
                .first()
            )

            business_admin = (
                User.objects
                .filter(
                    tenant=tenant,
                    role="business_admin"
                )
                .order_by(
                    "date_joined"
                )
                .first()
            )

            staff_count = (
                User.objects
                .filter(
                    tenant=tenant,
                    role="staff"
                )
                .count()
            )

            customer_count = (
                CustomerTenantMembership
                .objects
                .filter(
                    tenant=tenant,
                    status="active"
                )
                .count()
            )

            print_jobs_count = (
                PrintJob.objects
                .filter(
                    tenant=tenant
                )
                .count()
            )

            documents_count = (
                Document.objects
                .filter(
                    tenant=tenant
                )
                .count()
            )

            tenants_data.append({
                "id":
                    tenant.id,

                "name":
                    tenant.name,

                "slug":
                    tenant.slug,

                "subdomain":
                    tenant.subdomain,

                "custom_domain":
                    tenant.custom_domain,

                "email":
                    tenant.email,

                "phone_number":
                    tenant.phone_number,

                "address":
                    tenant.address,

                "logo":
                    tenant.logo,

                "is_active":
                    tenant.is_active,

                "created_at":
                    tenant.created_at,

                "updated_at":
                    tenant.updated_at,

                "portal_url":
                    tenant.portal_url,

                # --------------------------------------------
                # BUSINESS ADMIN
                # --------------------------------------------

                "business_admin": {
                    "id":
                        business_admin.id,

                    "full_name":
                        business_admin.full_name,

                    "email":
                        business_admin.email,

                    "phone_number":
                        business_admin.phone_number,

                    "is_active":
                        business_admin.is_active,
                }
                if business_admin
                else None,

                # --------------------------------------------
                # SUBSCRIPTION
                # --------------------------------------------

                "subscription": {
                    "id":
                        subscription.id,

                    "status":
                        subscription.status,

                    "plan": {
                        "id":
                            subscription.plan.id,

                        "name":
                            subscription.plan.name,

                        "slug":
                            subscription.plan.slug,

                        "monthly_price":
                            subscription.plan.monthly_price,

                        "yearly_price":
                            subscription.plan.yearly_price,
                    },

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

                    "auto_renew":
                        subscription.auto_renew,

                    "payment_method":
                        subscription.payment_method,

                    # Use this only if your Subscription
                    # model actually has this field.
                    "billing_cycle":
                        getattr(
                            subscription,
                            "billing_cycle",
                            None
                        ),
                }
                if subscription
                else None,

                # --------------------------------------------
                # STATS
                # --------------------------------------------

                "stats": {
                    "staff":
                        staff_count,

                    "customers":
                        customer_count,

                    "documents":
                        documents_count,

                    "print_jobs":
                        print_jobs_count,
                },
            })

        return Response({
            "success": True,

            "count":
                len(
                    tenants_data
                ),

            "tenants":
                tenants_data,
        })

    except Exception as error:

        print(
            "PLATFORM TENANTS ERROR:",
            error
        )

        return Response({
            "success": False,
            "message":
                "Unable to load businesses."
        }, status=500)


# ============================================================
# UPDATE TENANT STATUS
# ============================================================

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def platform_update_tenant_status(
    request,
    tenant_id
):
    error_response = (
        ensure_platform_admin(
            request
        )
    )

    if error_response:
        return error_response

    tenant = (
        Tenant.objects
        .filter(
            id=tenant_id
        )
        .first()
    )

    if not tenant:
        return Response({
            "success": False,
            "message":
                "Business not found."
        }, status=404)

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

    tenant.is_active = (
        is_active
    )

    tenant.save(
        update_fields=[
            "is_active",
            "updated_at",
        ]
    )

    return Response({
        "success": True,

        "message":
            (
                "Business activated successfully."
                if tenant.is_active
                else "Business deactivated successfully."
            ),

        "tenant": {
            "id":
                tenant.id,

            "name":
                tenant.name,

            "is_active":
                tenant.is_active,
        }
    })





@api_view(["GET"])
@permission_classes([IsAuthenticated])
def platform_tenant_detail(
    request,
    tenant_id
):
    error_response = (
        ensure_platform_admin(
            request
        )
    )

    if error_response:
        return error_response

    tenant = (
        Tenant.objects
        .filter(
            id=tenant_id
        )
        .first()
    )

    if not tenant:
        return Response({
            "success": False,
            "message":
                "Business not found."
        }, status=404)

    subscription = (
        Subscription.objects
        .filter(
            tenant=tenant
        )
        .select_related(
            "plan"
        )
        .first()
    )

    business_admin = (
        User.objects
        .filter(
            tenant=tenant,
            role="business_admin"
        )
        .order_by(
            "date_joined"
        )
        .first()
    )

    staff_count = (
        User.objects
        .filter(
            tenant=tenant,
            role="staff"
        )
        .count()
    )

    active_customers = (
        CustomerTenantMembership.objects
        .filter(
            tenant=tenant,
            status="active"
        )
        .count()
    )

    total_customers = (
        CustomerTenantMembership.objects
        .filter(
            tenant=tenant
        )
        .count()
    )

    total_documents = (
        Document.objects
        .filter(
            tenant=tenant
        )
        .count()
    )

    total_print_jobs = (
        PrintJob.objects
        .filter(
            tenant=tenant
        )
        .count()
    )

    printed_jobs = (
        PrintJob.objects
        .filter(
            tenant=tenant,
            status="printed"
        )
        .count()
    )

    queued_jobs = (
        PrintJob.objects
        .filter(
            tenant=tenant,
            status="queued"
        )
        .count()
    )

    printing_jobs = (
        PrintJob.objects
        .filter(
            tenant=tenant,
            status="printing"
        )
        .count()
    )

    failed_jobs = (
        PrintJob.objects
        .filter(
            tenant=tenant,
            status="failed"
        )
        .count()
    )

    total_customer_payments = (
        Payment.objects
        .filter(
            tenant=tenant,
            status="paid"
        )
        .aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    subscription_revenue = (
        SubscriptionPayment.objects
        .filter(
            tenant=tenant,
            status="paid"
        )
        .aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    recent_subscription_payments = (
        SubscriptionPayment.objects
        .filter(
            tenant=tenant
        )
        .select_related(
            "subscription",
            "subscription__plan",
        )
        .order_by(
            "-created_at"
        )[:5]
    )

    recent_subscription_payments_data = []

    for payment in recent_subscription_payments:
        recent_subscription_payments_data.append({
            "id":
                payment.id,

            "amount":
                payment.amount,

            "currency":
                payment.currency,

            "status":
                payment.status,

            "payment_method":
                payment.payment_method,

            "transaction_id":
                payment.transaction_id,

            "mpesa_receipt_number":
                payment.mpesa_receipt_number,

            "paid_at":
                payment.paid_at,

            "created_at":
                payment.created_at,

            "plan":
                payment.subscription.plan.name,
        })

    recent_print_jobs = (
        PrintJob.objects
        .filter(
            tenant=tenant
        )
        .select_related(
            "document",
            "user",
            "payment",
        )
        .order_by(
            "-created_at"
        )[:5]
    )

    recent_print_jobs_data = []

    for job in recent_print_jobs:
        payment = getattr(
            job,
            "payment",
            None
        )

        recent_print_jobs_data.append({
            "id":
                job.id,

            "status":
                job.status,

            "copies":
                job.copies,

            "paper_size":
                job.paper_size,

            "color":
                job.color,

            "double_sided":
                job.double_sided,

            "created_at":
                job.created_at,

            "customer": {
                "id":
                    job.user.id,

                "full_name":
                    job.user.full_name,

                "email":
                    job.user.email,
            },

            "document": {
                "id":
                    job.document.id,

                "name":
                    job.document.original_name,

                "pages":
                    job.document.pages,
            },

            "payment": {
                "id":
                    payment.id,

                "status":
                    payment.status,

                "amount":
                    payment.amount,
            }
            if payment
            else None,
        })

    return Response({
        "success": True,

        "tenant": {
            "id":
                tenant.id,

            "name":
                tenant.name,

            "slug":
                tenant.slug,

            "subdomain":
                tenant.subdomain,

            "custom_domain":
                tenant.custom_domain,

            "email":
                tenant.email,

            "phone_number":
                tenant.phone_number,

            "address":
                tenant.address,

            "logo":
                tenant.logo,

            "is_active":
                tenant.is_active,

            "created_at":
                tenant.created_at,

            "updated_at":
                tenant.updated_at,

            "portal_url":
                tenant.portal_url,
        },

        "business_admin": {
            "id":
                business_admin.id,

            "full_name":
                business_admin.full_name,

            "email":
                business_admin.email,

            "phone_number":
                business_admin.phone_number,

            "is_active":
                business_admin.is_active,

            "date_joined":
                business_admin.date_joined,
        }
        if business_admin
        else None,

        "subscription": {
    "id":
        subscription.id,

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

    "auto_renew":
        subscription.auto_renew,

    "payment_method":
        subscription.payment_method,

    "billing_cycle":
        getattr(
            subscription,
            "billing_cycle",
            None
        ),

    "plan": {
        "id":
            subscription.plan.id,

        "name":
            subscription.plan.name,

        "slug":
            subscription.plan.slug,

        "monthly_price":
            subscription.plan.monthly_price,

        "yearly_price":
            subscription.plan.yearly_price,

        "max_users":
            subscription.plan.max_users,

        "max_documents":
            subscription.plan.max_documents,

        "max_print_jobs":
            subscription.plan.max_print_jobs,

        "max_storage_mb":
            subscription.plan.max_storage_mb,

        "allow_color_printing":
            subscription.plan.allow_color_printing,

        "allow_double_sided":
            subscription.plan.allow_double_sided,

        "allow_multiple_printers":
            subscription.plan.allow_multiple_printers,

        "allow_staff_accounts":
            subscription.plan.allow_staff_accounts,

        "allow_custom_domain":
            subscription.plan.allow_custom_domain,

        "advanced_reports":
            subscription.plan.advanced_reports,

        "api_access":
            subscription.plan.api_access,

        "priority_support":
            subscription.plan.priority_support,
       },
       }

        if subscription
        else None,

        "stats": {
            "staff":
                staff_count,

            "customers":
                total_customers,

            "active_customers":
                active_customers,

            "documents":
                total_documents,

            "print_jobs":
                total_print_jobs,

            "printed_jobs":
                printed_jobs,

            "queued_jobs":
                queued_jobs,

            "printing_jobs":
                printing_jobs,

            "failed_jobs":
                failed_jobs,

            "customer_payment_volume":
                total_customer_payments,

            "subscription_revenue":
                subscription_revenue,
        },

        "recent_subscription_payments":
            recent_subscription_payments_data,

        "recent_print_jobs":
            recent_print_jobs_data,
    })


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def platform_update_tenant(
    request,
    tenant_id
):
    error_response = (
        ensure_platform_admin(
            request
        )
    )

    if error_response:
        return error_response

    tenant = (
        Tenant.objects
        .filter(
            id=tenant_id
        )
        .first()
    )

    if not tenant:
        return Response({
            "success": False,
            "message":
                "Business not found."
        }, status=404)

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

    custom_domain = request.data.get(
        "custom_domain",
        tenant.custom_domain
    )

    if isinstance(
        name,
        str
    ):
        name = name.strip()

    if isinstance(
        email,
        str
    ):
        email = email.strip().lower()

    if isinstance(
        phone_number,
        str
    ):
        phone_number = (
            phone_number.strip()
        )

    if isinstance(
        address,
        str
    ):
        address = (
            address.strip()
        )

    if isinstance(
        custom_domain,
        str
    ):
        custom_domain = (
            custom_domain.strip()
            or None
        )

    if not name:
        return Response({
            "success": False,
            "message":
                "Business name is required."
        }, status=400)

    if not email:
        return Response({
            "success": False,
            "message":
                "Business email is required."
        }, status=400)

    if (
        custom_domain
        and Tenant.objects
        .filter(
            custom_domain=
                custom_domain
        )
        .exclude(
            id=tenant.id
        )
        .exists()
    ):
        return Response({
            "success": False,
            "message":
                "This custom domain is already in use."
        }, status=400)

    tenant.name = name
    tenant.email = email
    tenant.phone_number = (
        phone_number
    )
    tenant.address = address
    tenant.custom_domain = (
        custom_domain
    )

    tenant.save(
        update_fields=[
            "name",
            "email",
            "phone_number",
            "address",
            "custom_domain",
            "updated_at",
        ]
    )

    return Response({
        "success": True,

        "message":
            "Business information updated successfully.",

        "tenant": {
            "id":
                tenant.id,

            "name":
                tenant.name,

            "email":
                tenant.email,

            "phone_number":
                tenant.phone_number,

            "address":
                tenant.address,

            "custom_domain":
                tenant.custom_domain,
        }
    })