from .common_imports import *


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def customer_dashboard(request):

    user = request.user

    # ============================================================
    # ONLY CUSTOMERS
    # ============================================================

    if user.role != "customer":

        return Response({
            "message":
                "You are not allowed to access the customer dashboard."
        }, status=403)


    # ============================================================
    # GET ACTIVE TENANT
    # ============================================================
    #
    # Frontend sends:
    #
    # X-Tenant-Slug: gtech-company
    #
    # The customer itself no longer has user.tenant.
    # ============================================================

    tenant_slug = (
        request.headers
        .get(
            "X-Tenant-Slug",
            ""
        )
        .strip()
    )


    if not tenant_slug:

        return Response({
            "message":
                "Printing business could not be identified."
        }, status=400)


    tenant = Tenant.objects.filter(
        slug=tenant_slug,
        is_active=True
    ).first()


    if not tenant:

        return Response({
            "message":
                "Printing business not found."
        }, status=404)


    # ============================================================
    # VERIFY CUSTOMER MEMBERSHIP
    # ============================================================

    membership = (
        CustomerTenantMembership
        .objects
        .filter(
            customer=user,
            tenant=tenant
        )
        .first()
    )


    if not membership:

        return Response({
            "message":
                f"Your account is not connected to {tenant.name}."
        }, status=403)


    if membership.status == "blocked":

        return Response({
            "message":
                f"Your account has been blocked from using {tenant.name}."
        }, status=403)


    if membership.status != "active":

        return Response({
            "message":
                f"Your access to {tenant.name} is currently inactive."
        }, status=403)


    # ============================================================
    # DOCUMENTS
    # ============================================================

    documents = (
        Document.objects
        .filter(
            tenant=tenant,
            user=user,
        )
    )


    total_documents = (
        documents.count()
    )


    # ============================================================
    # PRINT JOBS
    # ============================================================

    jobs = (
        PrintJob.objects
        .filter(
            tenant=tenant,
            user=user,
        )
    )


    total_jobs = (
        jobs.count()
    )


    active_jobs = (
        jobs
        .filter(
            status__in=[
                "paid",
                "queued",
                "printing",
            ]
        )
        .count()
    )


    pending_jobs = (
        jobs
        .filter(
            status="pending"
        )
        .count()
    )


    completed_jobs = (
        jobs
        .filter(
            status="printed"
        )
        .count()
    )


    failed_jobs = (
        jobs
        .filter(
            status="failed"
        )
        .count()
    )


    cancelled_jobs = (
        jobs
        .filter(
            status="cancelled"
        )
        .count()
    )


    # ============================================================
    # PAYMENTS / TOTAL SPENT
    # ============================================================

    total_spent = (

        Payment.objects
        .filter(
            tenant=tenant,
            user=user,
            status="paid",
        )
        .aggregate(
            total=Sum("amount")
        )["total"]

        or Decimal("0.00")
    )


    # ============================================================
    # RECENT PRINT JOBS
    # ============================================================

    recent_jobs = (

        jobs
        .select_related(
            "document",
            "printer",
        )
        .order_by(
            "-created_at"
        )[:5]
    )


    recent_jobs_data = []


    for job in recent_jobs:

        payment = getattr(
            job,
            "payment",
            None
        )

        printer = getattr(
            job,
            "printer",
            None
        )


        recent_jobs_data.append({

            "id":
                job.id,


            "document": {

                "id":
                    job.document.id,

                "name":
                    job.document.original_name,

                "pages":
                    job.document.pages,

                "url":
                    job.document.cloudinary_url,

                "mime_type":
                    job.document.mime_type,

            },


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
                else Decimal("0.00"),


            "payment_status":
                payment.status
                if payment
                else None,


            "payment_method":
                payment.payment_method
                if payment
                else None,


            "printer": {

                "id":
                    printer.id,

                "name":
                    printer.name,

                "status":
                    printer.status,

            }
            if printer
            else None,


            "created_at":
                job.created_at,


            "updated_at":
                job.updated_at,

        })


    # ============================================================
    # RECENT DOCUMENTS
    # ============================================================

    recent_documents = (

        documents
        .order_by(
            "-uploaded_at"
        )[:5]
    )


    recent_documents_data = []


    for document in recent_documents:

        total_document_jobs = (
            PrintJob.objects
            .filter(
                tenant=tenant,
                user=user,
                document=document
            )
            .count()
        )


        recent_documents_data.append({

            "id":
                document.id,


            "name":
                document.original_name,


            "pages":
                document.pages,


            "size":
                document.size,


            "mime_type":
                document.mime_type,


            "status":
                document.status,


            "url":
                document.cloudinary_url,


            "total_print_jobs":
                total_document_jobs,


            "uploaded_at":
                document.uploaded_at,

        })


    # ============================================================
    # RESPONSE
    # ============================================================

    return Response({

        "success": True,


        # --------------------------------------------------------
        # Customer
        # --------------------------------------------------------

        "customer": {

            "id":
                user.id,

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

        },


        # --------------------------------------------------------
        # Current business
        # --------------------------------------------------------

        "business": {

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

            "phone_number":
                tenant.phone_number,

            "email":
                tenant.email,

            "address":
                tenant.address,

            "custom_domain":
                tenant.custom_domain,

        },


        # --------------------------------------------------------
        # Membership
        # --------------------------------------------------------

        "membership": {

            "id":
                membership.id,

            "status":
                membership.status,

            "joined_at":
                membership.joined_at,

        },


        # --------------------------------------------------------
        # Dashboard stats
        # --------------------------------------------------------

        "stats": {

            "documents":
                total_documents,

            "print_jobs":
                total_jobs,

            "active_jobs":
                active_jobs,

            "pending_jobs":
                pending_jobs,

            "completed_jobs":
                completed_jobs,

            "failed_jobs":
                failed_jobs,

            "cancelled_jobs":
                cancelled_jobs,

            "total_spent":
                total_spent,

        },


        # --------------------------------------------------------
        # Recent activity
        # --------------------------------------------------------

        "recent_jobs":
            recent_jobs_data,


        "recent_documents":
            recent_documents_data,

    })