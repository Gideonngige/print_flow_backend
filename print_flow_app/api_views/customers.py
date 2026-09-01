from .common_imports import *


# ============================================================
# LIST BUSINESS CUSTOMERS
# ============================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def business_customers(request):

    user = request.user

    if user.role not in [
        "business_admin",
        "staff",
    ]:
        return Response({
            "message":
                "You are not allowed to access customers."
        }, status=403)

    tenant = user.tenant

    if not tenant:
        return Response({
            "message":
                "Your account is not linked to a business."
        }, status=400)

    search = (
        request.GET.get(
            "search",
            ""
        )
        .strip()
    )

    customers = User.objects.filter(
        tenant=tenant,
        role="customer"
    )

    if search:
        customers = customers.filter(
            Q(full_name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone_number__icontains=search)
        )

    customers = customers.order_by(
        "-date_joined"
    )

    customer_data = []

    for customer in customers:

        total_jobs = PrintJob.objects.filter(
            tenant=tenant,
            user=customer
        ).count()

        completed_jobs = PrintJob.objects.filter(
            tenant=tenant,
            user=customer,
            status="printed"
        ).count()

        total_spent = (
            Payment.objects
            .filter(
                tenant=tenant,
                user=customer,
                status="paid",
            )
            .aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

        customer_data.append({
            "id": customer.id,
            "full_name": customer.full_name,
            "email": customer.email,
            "phone_number":
                customer.phone_number,

            "email_verified":
                customer.email_verified,

            "phone_verified":
                customer.phone_verified,

            "is_active":
                customer.is_active,

            "date_joined":
                customer.date_joined,

            "total_jobs":
                total_jobs,

            "completed_jobs":
                completed_jobs,

            "total_spent":
                total_spent,
        })

    return Response({
        "success": True,
        "count": len(customer_data),
        "customers": customer_data,
    })


# ============================================================
# CUSTOMER DETAILS
# ============================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def business_customer_detail(
    request,
    customer_id
):

    user = request.user

    if user.role not in [
        "business_admin",
        "staff",
    ]:
        return Response({
            "message":
                "You are not allowed to access this customer."
        }, status=403)

    tenant = user.tenant

    customer = User.objects.filter(
        id=customer_id,
        tenant=tenant,
        role="customer"
    ).first()

    if not customer:
        return Response({
            "message":
                "Customer not found."
        }, status=404)

    jobs = (
        PrintJob.objects
        .filter(
            tenant=tenant,
            user=customer
        )
        .select_related(
            "document"
        )
        .order_by(
            "-created_at"
        )[:10]
    )

    jobs_data = []

    for job in jobs:

        payment = getattr(
            job,
            "payment",
            None
        )

        jobs_data.append({
            "id": job.id,
            "document":
                job.document.original_name,

            "pages":
                job.document.pages,

            "copies":
                job.copies,

            "paper_size":
                job.paper_size,

            "color":
                job.color,

            "double_sided":
                job.double_sided,

            "status":
                job.status,

            "amount":
                payment.amount
                if payment
                else 0,

            "created_at":
                job.created_at,
        })

    total_spent = (
        Payment.objects
        .filter(
            tenant=tenant,
            user=customer,
            status="paid"
        )
        .aggregate(
            total=Sum("amount")
        )["total"]
        or 0
    )

    total_jobs = PrintJob.objects.filter(
        tenant=tenant,
        user=customer
    ).count()

    completed_jobs = PrintJob.objects.filter(
        tenant=tenant,
        user=customer,
        status="printed"
    ).count()

    return Response({
        "success": True,

        "customer": {
            "id": customer.id,

            "full_name":
                customer.full_name,

            "email":
                customer.email,

            "phone_number":
                customer.phone_number,

            "email_verified":
                customer.email_verified,

            "phone_verified":
                customer.phone_verified,

            "is_active":
                customer.is_active,

            "date_joined":
                customer.date_joined,

            "total_jobs":
                total_jobs,

            "completed_jobs":
                completed_jobs,

            "total_spent":
                total_spent,

            "recent_jobs":
                jobs_data,
        }
    })


# ============================================================
# ACTIVATE / DISABLE CUSTOMER
# ============================================================

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_customer_status(
    request,
    customer_id
):

    user = request.user

    # Only business admin should disable users
    if user.role != "business_admin":
        return Response({
            "message":
                "Only the business administrator "
                "can change customer status."
        }, status=403)

    tenant = user.tenant

    customer = User.objects.filter(
        id=customer_id,
        tenant=tenant,
        role="customer"
    ).first()

    if not customer:
        return Response({
            "message":
                "Customer not found."
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

    customer.is_active = is_active

    customer.save(
        update_fields=[
            "is_active"
        ]
    )

    return Response({
        "success": True,

        "message":
            "Customer status updated successfully.",

        "customer": {
            "id":
                customer.id,

            "is_active":
                customer.is_active,
        }
    })