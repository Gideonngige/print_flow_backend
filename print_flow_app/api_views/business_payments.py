from .common_imports import *


# ============================================================
# LIST BUSINESS PAYMENTS
# ============================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def business_payments(request):
    user = request.user

    if user.role not in [
        "business_admin",
        "staff",
    ]:
        return Response({
            "message":
                "You are not allowed to access payments."
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

    status_filter = (
        request.GET.get(
            "status",
            ""
        )
        .strip()
    )

    method_filter = (
        request.GET.get(
            "method",
            ""
        )
        .strip()
    )

    payments = (
        Payment.objects
        .filter(
            tenant=tenant
        )
        .select_related(
            "user",
            "print_job",
            "print_job__document",
        )
        .order_by(
            "-created_at"
        )
    )

    # --------------------------------------------------------
    # Search
    # --------------------------------------------------------

    if search:
        payments = payments.filter(
            Q(
                user__full_name__icontains=
                    search
            )
            |
            Q(
                user__email__icontains=
                    search
            )
            |
            Q(
                user__phone_number__icontains=
                    search
            )
            |
            Q(
                transaction_id__icontains=
                    search
            )
            |
            Q(
                mpesa_receipt_number__icontains=
                    search
            )
            |
            Q(
                print_job__document__original_name__icontains=
                    search
            )
        )

    # --------------------------------------------------------
    # Filters
    # --------------------------------------------------------

    valid_statuses = [
        "pending",
        "paid",
        "failed",
        "cancelled",
    ]

    if (
        status_filter and
        status_filter in valid_statuses
    ):
        payments = payments.filter(
            status=status_filter
        )

    valid_methods = [
        "m-pesa",
        "paystack",
    ]

    if (
        method_filter and
        method_filter in valid_methods
    ):
        payments = payments.filter(
            payment_method=method_filter
        )

    data = []

    for payment in payments:
        print_job = payment.print_job
        document = print_job.document

        data.append({
            "id":
                payment.id,

            "amount":
                payment.amount,

            "subtotal":
                payment.subtotal,

            "color_charge":
                payment.color_charge,

            "paper_charge":
                payment.paper_charge,

            "discount":
                payment.discount,

            "payment_method":
                payment.payment_method,

            "status":
                payment.status,

            "transaction_id":
                payment.transaction_id,

            "mpesa_receipt_number":
                payment.mpesa_receipt_number,

            "checkout_request_id":
                payment.checkout_request_id,

            "created_at":
                payment.created_at,

            "paid_at":
                payment.paid_at,

            "customer": {
                "id":
                    payment.user.id,

                "name":
                    payment.user.full_name,

                "email":
                    payment.user.email,

                "phone_number":
                    payment.user.phone_number,
            },

            "print_job": {
                "id":
                    print_job.id,

                "status":
                    print_job.status,

                "copies":
                    print_job.copies,

                "paper_size":
                    print_job.paper_size,

                "color":
                    print_job.color,

                "double_sided":
                    print_job.double_sided,
            },

            "document": {
                "id":
                    document.id,

                "name":
                    document.original_name,

                "pages":
                    document.pages,
            }
        })

    # --------------------------------------------------------
    # Stats
    # --------------------------------------------------------

    base = Payment.objects.filter(
        tenant=tenant
    )

    total_revenue = (
        base.filter(
            status="paid"
        )
        .aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    today = timezone.localdate()

    today_revenue = (
        base.filter(
            status="paid",
            paid_at__date=today
        )
        .aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    stats = {
        "total":
            base.count(),

        "paid":
            base.filter(
                status="paid"
            ).count(),

        "pending":
            base.filter(
                status="pending"
            ).count(),

        "failed":
            base.filter(
                status="failed"
            ).count(),

        "cancelled":
            base.filter(
                status="cancelled"
            ).count(),

        "total_revenue":
            total_revenue,

        "today_revenue":
            today_revenue,
    }

    return Response({
        "success": True,
        "count": len(data),
        "stats": stats,
        "payments": data,
    })


# ============================================================
# BUSINESS PAYMENT DETAIL
# ============================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def business_payment_detail(
    request,
    payment_id
):
    user = request.user

    if user.role not in [
        "business_admin",
        "staff",
    ]:
        return Response({
            "message":
                "You are not allowed to access this payment."
        }, status=403)

    tenant = user.tenant

    payment = (
        Payment.objects
        .filter(
            id=payment_id,
            tenant=tenant
        )
        .select_related(
            "user",
            "print_job",
            "print_job__document",
        )
        .first()
    )

    if not payment:
        return Response({
            "message":
                "Payment not found."
        }, status=404)

    job = payment.print_job
    document = job.document

    return Response({
        "success": True,

        "payment": {
            "id":
                payment.id,

            "amount":
                payment.amount,

            "subtotal":
                payment.subtotal,

            "color_charge":
                payment.color_charge,

            "paper_charge":
                payment.paper_charge,

            "discount":
                payment.discount,

            "payment_method":
                payment.payment_method,

            "status":
                payment.status,

            "transaction_id":
                payment.transaction_id,

            "mpesa_receipt_number":
                payment.mpesa_receipt_number,

            "checkout_request_id":
                payment.checkout_request_id,

            "created_at":
                payment.created_at,

            "paid_at":
                payment.paid_at,

            "customer": {
                "id":
                    payment.user.id,

                "name":
                    payment.user.full_name,

                "email":
                    payment.user.email,

                "phone_number":
                    payment.user.phone_number,
            },

            "print_job": {
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
            },

            "document": {
                "id":
                    document.id,

                "name":
                    document.original_name,

                "pages":
                    document.pages,

                "url":
                    document.cloudinary_url,
            }
        }
    })