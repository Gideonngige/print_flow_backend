from .common_imports import *


# ============================================================
# HELPER: GET ACTIVE CUSTOMER TENANT
# ============================================================

def get_active_customer_tenant(request):
    user = request.user

    if user.role != "customer":
        return None, Response({
            "success": False,
            "message":
                "Only customer accounts can access this resource."
        }, status=403)

    tenant_slug = (
        request.headers
        .get(
            "X-Tenant-Slug",
            ""
        )
        .strip()
    )

    if not tenant_slug:
        return None, Response({
            "success": False,
            "message":
                "Printing business could not be identified."
        }, status=400)

    tenant = Tenant.objects.filter(
        slug=tenant_slug,
        is_active=True
    ).first()

    if not tenant:
        return None, Response({
            "success": False,
            "message":
                "Printing business not found."
        }, status=404)

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
        return None, Response({
            "success": False,
            "message":
                f"Your account is not connected to {tenant.name}."
        }, status=403)

    if membership.status == "blocked":
        return None, Response({
            "success": False,
            "message":
                f"Your account has been blocked from using {tenant.name}."
        }, status=403)

    if membership.status != "active":
        return None, Response({
            "success": False,
            "message":
                f"Your access to {tenant.name} is currently inactive."
        }, status=403)

    return tenant, None


# ============================================================
# UPLOAD DOCUMENT
# ============================================================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upload_document(request):

    tenant, error_response = (
        get_active_customer_tenant(
            request
        )
    )

    if error_response:
        return error_response

    uploaded_file = request.FILES.get(
        "file"
    )

    if not uploaded_file:
        return Response({
            "success": False,
            "message":
                "Please select a document."
        }, status=400)

    # --------------------------------------------------------
    # Allowed file types
    # --------------------------------------------------------

    allowed_extensions = [
        ".pdf",
        ".doc",
        ".docx",
        ".ppt",
        ".pptx",
        ".xls",
        ".xlsx",
        ".txt",
        ".jpg",
        ".jpeg",
        ".png",
    ]

    extension = (
        os.path.splitext(
            uploaded_file.name
        )[1]
        .lower()
    )

    if extension not in allowed_extensions:
        return Response({
            "success": False,
            "message":
                "Unsupported file type."
        }, status=400)

    # --------------------------------------------------------
    # Maximum size: 30 MB
    # --------------------------------------------------------

    if uploaded_file.size > (
        30 * 1024 * 1024
    ):
        return Response({
            "success": False,
            "message":
                "Maximum file size is 30 MB."
        }, status=400)

    # --------------------------------------------------------
    # Count pages
    # --------------------------------------------------------

    pages = 1

    if extension == ".pdf":
        try:
            reader = PdfReader(
                uploaded_file
            )

            pages = len(
                reader.pages
            )

            uploaded_file.seek(0)

        except Exception as error:
            print(
                "PDF page count error:",
                error
            )

            uploaded_file.seek(0)
            pages = 1

    # --------------------------------------------------------
    # Upload to Cloudinary
    # --------------------------------------------------------

    try:
        result = (
            cloudinary.uploader.upload(
                uploaded_file,
                folder=(
                    f"printflow/"
                    f"{tenant.slug}/documents"
                ),
                resource_type="raw",
                use_filename=True,
                unique_filename=True,
            )
        )

        document = (
            Document.objects.create(
                tenant=tenant,
                user=request.user,

                original_name=
                    uploaded_file.name,

                cloudinary_public_id=
                    result["public_id"],

                cloudinary_url=
                    result["secure_url"],

                mime_type=
                    uploaded_file.content_type
                    or "",

                size=
                    uploaded_file.size,

                pages=
                    pages,

                status=
                    "uploaded",
            )
        )

        return Response({
            "success": True,

            "message":
                "Document uploaded successfully.",

            "document": {
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

                "uploaded_at":
                    document.uploaded_at,
            }

        }, status=201)

    except Exception as error:

        print(
            "Document upload error:",
            error
        )

        return Response({
            "success": False,
            "message":
                "Unable to upload the document."
        }, status=500)


# ============================================================
# CREATE PRINT JOB
# ============================================================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_print_job(request):

    tenant, error_response = (
        get_active_customer_tenant(
            request
        )
    )

    if error_response:
        return error_response

    document_id = request.data.get(
        "document_id"
    )

    if not document_id:
        return Response({
            "success": False,
            "message":
                "Document ID is required."
        }, status=400)

    # --------------------------------------------------------
    # Copies
    # --------------------------------------------------------

    try:
        copies = int(
            request.data.get(
                "copies",
                1
            )
        )

    except (
        TypeError,
        ValueError
    ):
        return Response({
            "success": False,
            "message":
                "Copies must be a valid number."
        }, status=400)

    if copies < 1:
        return Response({
            "success": False,
            "message":
                "Copies must be at least 1."
        }, status=400)

    if copies > 100:
        return Response({
            "success": False,
            "message":
                "Copies cannot exceed 100."
        }, status=400)

    paper_size = (
        str(
            request.data.get(
                "paper_size",
                "A4"
            )
        )
        .strip()
        .upper()
    )

    color = request.data.get(
        "color",
        False
    )

    double_sided = request.data.get(
        "double_sided",
        False
    )

    payment_method = request.data.get(
        "payment_method",
        "m-pesa"
    )

    # Normalize boolean values safely
    if isinstance(color, str):
        color = (
            color.lower()
            in [
                "true",
                "1",
                "yes",
            ]
        )

    if isinstance(
        double_sided,
        str
    ):
        double_sided = (
            double_sided.lower()
            in [
                "true",
                "1",
                "yes",
            ]
        )

    if payment_method not in [
        "m-pesa",
        "paystack",
    ]:
        return Response({
            "success": False,
            "message":
                "Invalid payment method."
        }, status=400)

    # --------------------------------------------------------
    # Document
    # --------------------------------------------------------

    document = (
        Document.objects
        .filter(
            id=document_id,
            tenant=tenant,
            user=request.user
        )
        .first()
    )

    if not document:
        return Response({
            "success": False,
            "message":
                "Document not found."
        }, status=404)

    # --------------------------------------------------------
    # Prevent bad page count
    # --------------------------------------------------------

    pages = max(
        int(
            document.pages or 1
        ),
        1
    )

    # --------------------------------------------------------
    # Resolve pricing
    # --------------------------------------------------------

    print_type = (
        "color"
        if color
        else "black_white"
    )

    sides = (
        "double"
        if double_sided
        else "single"
    )

    pricing = (
        Pricing.objects
        .filter(
            tenant=tenant,
            paper_size=paper_size,
            print_type=print_type,
            sides=sides,
            is_active=True,
        )
        .first()
    )

    if not pricing:
        return Response({
            "success": False,

            "message":
                (
                    "This printing option is "
                    "not currently available."
                )
        }, status=400)

    # --------------------------------------------------------
    # Calculate amount
    # --------------------------------------------------------

    total_pages = (
        pages * copies
    )

    subtotal = (
        Decimal(total_pages)
        *
        pricing.price_per_page
    )

    minimum_charge = (
        pricing.minimum_charge
        or Decimal("0.00")
    )

    total = max(
        subtotal,
        minimum_charge
    )

    # Keep compatibility with your Payment model fields.
    color_charge = Decimal(
        "0.00"
    )

    paper_charge = Decimal(
        "0.00"
    )

    discount = Decimal(
        "0.00"
    )

    # --------------------------------------------------------
    # Create print job
    # --------------------------------------------------------

    try:
        with transaction.atomic():

            print_job = (
                PrintJob.objects.create(
                    tenant=tenant,
                    user=request.user,
                    document=document,

                    copies=copies,
                    paper_size=paper_size,
                    color=color,
                    double_sided=
                        double_sided,

                    status="pending"
                )
            )

            payment = (
                Payment.objects.create(
                    tenant=tenant,
                    user=request.user,
                    print_job=print_job,

                    subtotal=subtotal,
                    paper_charge=
                        paper_charge,
                    color_charge=
                        color_charge,
                    discount=
                        discount,

                    amount=total,

                    payment_method=
                        payment_method,

                    status="pending"
                )
            )

    except Exception as error:

        print(
            "Create print job error:",
            error
        )

        return Response({
            "success": False,

            "message":
                "Unable to create print job."
        }, status=500)

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return Response({
        "success": True,

        "message":
            "Print job created successfully.",

        "print_job": {
            "id":
                print_job.id,

            "document_id":
                document.id,

            "document":
                document.original_name,

            "pages":
                document.pages,

            "copies":
                print_job.copies,

            "paper_size":
                print_job.paper_size,

            "color":
                print_job.color,

            "double_sided":
                print_job.double_sided,

            "status":
                print_job.status,
        },

        "pricing": {
            "id":
                pricing.id,

            "price_per_page":
                pricing.price_per_page,

            "minimum_charge":
                pricing.minimum_charge,

            "total_pages":
                total_pages,
        },

        "payment": {
            "id":
                payment.id,

            "subtotal":
                payment.subtotal,

            "paper_charge":
                payment.paper_charge,

            "color_charge":
                payment.color_charge,

            "discount":
                payment.discount,

            "amount":
                payment.amount,

            "payment_method":
                payment.payment_method,

            "status":
                payment.status,
        }

    }, status=201)


# ============================================================
# MY DOCUMENTS
# ============================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_documents(request):

    tenant, error_response = (
        get_active_customer_tenant(
            request
        )
    )

    if error_response:
        return error_response

    try:
        documents = (
            Document.objects
            .filter(
                tenant=tenant,
                user=request.user
            )
            .prefetch_related(
                Prefetch(
                    "print_jobs",
                    queryset=(
                        PrintJob.objects
                        .filter(
                            tenant=tenant,
                            user=request.user
                        )
                        .order_by(
                            "-created_at"
                        )
                    )
                )
            )
            .order_by(
                "-uploaded_at"
            )
        )

        documents_data = []

        for document in documents:

            print_jobs = list(
                document.print_jobs.all()
            )

            latest_job = (
                print_jobs[0]
                if print_jobs
                else None
            )

            current_status = (
                latest_job.status
                if latest_job
                else document.status
            )

            documents_data.append({
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
                    current_status,

                "document_status":
                    document.status,

                "url":
                    document.cloudinary_url,

                "uploaded_at":
                    document.uploaded_at,

                "total_print_jobs":
                    len(print_jobs),

                "latest_print_job": {
                    "id":
                        latest_job.id,

                    "copies":
                        latest_job.copies,

                    "paper_size":
                        latest_job.paper_size,

                    "color":
                        latest_job.color,

                    "double_sided":
                        latest_job.double_sided,

                    "status":
                        latest_job.status,

                    "created_at":
                        latest_job.created_at,

                }
                if latest_job
                else None,
            })

        return Response({
            "success": True,
            "count":
                len(documents_data),
            "documents":
                documents_data,
        })

    except Exception as error:

        print(
            "My documents error:",
            error
        )

        return Response({
            "success": False,
            "message":
                "Unable to load documents."
        }, status=500)


# ============================================================
# DELETE DOCUMENT
# ============================================================

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_document(
    request,
    document_id
):

    tenant, error_response = (
        get_active_customer_tenant(
            request
        )
    )

    if error_response:
        return error_response

    try:
        document = (
            Document.objects
            .filter(
                id=document_id,
                tenant=tenant,
                user=request.user,
            )
            .first()
        )

        if not document:
            return Response({
                "success": False,
                "message":
                    "Document not found."
            }, status=404)

        # ----------------------------------------------------
        # Block deletion while job is active
        # ----------------------------------------------------

        active_job_exists = (
            PrintJob.objects
            .filter(
                tenant=tenant,
                user=request.user,
                document=document,
                status__in=[
                    "paid",
                    "queued",
                    "printing",
                ],
            )
            .exists()
        )

        if active_job_exists:
            return Response({
                "success": False,

                "message":
                    (
                        "This document cannot be deleted "
                        "because it has an active print job."
                    )

            }, status=400)

        # ----------------------------------------------------
        # Remove Cloudinary file
        # ----------------------------------------------------

        if (
            document.cloudinary_public_id
        ):
            try:
                cloudinary.uploader.destroy(
                    document.cloudinary_public_id,
                    resource_type="raw",
                    invalidate=True,
                )

            except Exception as cloudinary_error:

                print(
                    "Cloudinary deletion error:",
                    cloudinary_error,
                )

        # ----------------------------------------------------
        # Delete database record
        # ----------------------------------------------------

        document.delete()

        return Response({
            "success": True,
            "message":
                "Document deleted successfully."
        })

    except Exception as error:

        print(
            "Delete document error:",
            error
        )

        return Response({
            "success": False,
            "message":
                "Unable to delete document."
        }, status=500)