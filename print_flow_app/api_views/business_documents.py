from .common_imports import *


# ============================================================
# LIST BUSINESS DOCUMENTS
# ============================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def business_documents(request):

    user = request.user

    if user.role not in [
        "business_admin",
        "staff",
    ]:
        return Response({
            "message":
                "You are not allowed to access documents."
        }, status=403)

    tenant = user.tenant

    if not tenant:
        return Response({
            "message":
                "Your account is not linked to a business."
        }, status=400)

    search = (
        request.GET.get("search", "")
        .strip()
    )

    status_filter = (
        request.GET.get("status", "")
        .strip()
    )

    documents = (
        Document.objects
        .filter(
            tenant=tenant
        )
        .select_related(
            "user"
        )
        .order_by(
            "-uploaded_at"
        )
    )

    if search:
        documents = documents.filter(
            Q(
                original_name__icontains=
                    search
            )
            |
            Q(
                user__full_name__icontains=
                    search
            )
            |
            Q(
                user__email__icontains=
                    search
            )
        )

    valid_statuses = [
        "uploaded",
        "pending",
        "printing",
        "printed",
        "failed",
    ]

    if (
        status_filter and
        status_filter in valid_statuses
    ):
        documents = documents.filter(
            status=status_filter
        )

    documents_data = []

    for document in documents:

        total_jobs = PrintJob.objects.filter(
            tenant=tenant,
            document=document
        ).count()

        documents_data.append({
            "id":
                document.id,

            "name":
                document.original_name,

            "mime_type":
                document.mime_type,

            "size":
                document.size,

            "pages":
                document.pages,

            "status":
                document.status,

            "url":
                document.cloudinary_url,

            "cloudinary_public_id":
                document.cloudinary_public_id,

            "uploaded_at":
                document.uploaded_at,

            "total_print_jobs":
                total_jobs,

            "customer": {
                "id":
                    document.user.id,

                "name":
                    document.user.full_name,

                "email":
                    document.user.email,

                "phone_number":
                    document.user.phone_number,
            }
        })

    base_documents = Document.objects.filter(
        tenant=tenant
    )

    stats = {
        "total":
            base_documents.count(),

        "uploaded":
            base_documents.filter(
                status="uploaded"
            ).count(),

        "pending":
            base_documents.filter(
                status="pending"
            ).count(),

        "printing":
            base_documents.filter(
                status="printing"
            ).count(),

        "printed":
            base_documents.filter(
                status="printed"
            ).count(),

        "failed":
            base_documents.filter(
                status="failed"
            ).count(),
    }

    return Response({
        "success": True,
        "count": len(documents_data),
        "stats": stats,
        "documents": documents_data,
    })


# ============================================================
# BUSINESS DOCUMENT DETAIL
# ============================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def business_document_detail(
    request,
    document_id
):

    user = request.user

    if user.role not in [
        "business_admin",
        "staff",
    ]:
        return Response({
            "message":
                "You are not allowed to access this document."
        }, status=403)

    tenant = user.tenant

    document = (
        Document.objects
        .filter(
            id=document_id,
            tenant=tenant
        )
        .select_related(
            "user"
        )
        .first()
    )

    if not document:
        return Response({
            "message":
                "Document not found."
        }, status=404)

    jobs = (
        PrintJob.objects
        .filter(
            tenant=tenant,
            document=document
        )
        .order_by(
            "-created_at"
        )
    )

    jobs_data = []

    for job in jobs:

        payment = getattr(
            job,
            "payment",
            None
        )

        jobs_data.append({
            "id":
                job.id,

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

            "payment_status":
                payment.status
                if payment
                else None,

            "created_at":
                job.created_at,
        })

    return Response({
        "success": True,

        "document": {
            "id":
                document.id,

            "name":
                document.original_name,

            "mime_type":
                document.mime_type,

            "size":
                document.size,

            "pages":
                document.pages,

            "status":
                document.status,

            "url":
                document.cloudinary_url,

            "uploaded_at":
                document.uploaded_at,

            "customer": {
                "id":
                    document.user.id,

                "name":
                    document.user.full_name,

                "email":
                    document.user.email,

                "phone_number":
                    document.user.phone_number,
            },

            "print_jobs":
                jobs_data,
        }
    })


# ============================================================
# DELETE BUSINESS DOCUMENT
# ============================================================

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_business_document(
    request,
    document_id
):

    user = request.user

    if user.role != "business_admin":
        return Response({
            "message":
                "Only the business administrator "
                "can delete documents."
        }, status=403)

    tenant = user.tenant

    document = Document.objects.filter(
        id=document_id,
        tenant=tenant
    ).first()

    if not document:
        return Response({
            "message":
                "Document not found."
        }, status=404)

    active_jobs = PrintJob.objects.filter(
        tenant=tenant,
        document=document,
        status__in=[
            "pending",
            "paid",
            "queued",
            "printing",
        ]
    ).exists()

    if active_jobs:
        return Response({
            "message":
                "This document cannot be deleted "
                "while it has an active print job."
        }, status=400)

    document.delete()

    return Response({
        "success": True,
        "message":
            "Document deleted successfully."
    })