from .common_imports import *


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upload_document(request):

    uploaded_file = request.FILES.get("file")

    if not uploaded_file:
        return JsonResponse({
            "success": False,
            "message": "Please select a document."
        }, status=400)

    # Allowed file types
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

    extension = os.path.splitext(uploaded_file.name)[1].lower()

    if extension not in allowed_extensions:
        return JsonResponse({
            "success": False,
            "message": "Unsupported file type."
        }, status=400)

    # Maximum size (30 MB)
    if uploaded_file.size > 30 * 1024 * 1024:
        return JsonResponse({
            "success": False,
            "message": "Maximum file size is 30 MB."
        }, status=400)

    # Count PDF pages
    pages = 1

    if extension == ".pdf":
        try:
            reader = PdfReader(uploaded_file)
            pages = len(reader.pages)
            uploaded_file.seek(0)
        except Exception:
            uploaded_file.seek(0)
            pages = 1

    try:

        result = cloudinary.uploader.upload(
            uploaded_file,
            folder="printflow/documents",
            resource_type="raw",
            use_filename=True,
            unique_filename=True,
        )

        document = Document.objects.create(
            user=request.user,
            original_name=uploaded_file.name,
            file=result["secure_url"],   # Stores the Cloudinary URL
            cloudinary_public_id=result["public_id"],
            cloudinary_url=result["secure_url"],
            mime_type=uploaded_file.content_type,
            size=uploaded_file.size,
            pages=pages,
            status="uploaded",
        )

        return JsonResponse({
            "success": True,
            "message": "Document uploaded successfully.",
            "document": {
                "id": document.id,
                "name": document.original_name,
                "pages": document.pages,
                "size": document.size,
                "mime_type": document.mime_type,
                "status": document.status,
                "url": document.cloudinary_url,
                "uploaded_at": document.uploaded_at,
            }
        }, status=201)

    except Exception as e:

        return JsonResponse({
            "success": False,
            "message": str(e)
        }, status=500)




# create print job api
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_print_job(request):

    document_id = request.data.get("document_id")
    copies = int(request.data.get("copies", 1))
    paper_size = request.data.get("paper_size", "A4")
    color = request.data.get("color", False)
    double_sided = request.data.get("double_sided", False)
    payment_method = request.data.get("payment_method", "m-pesa")

    document = Document.objects.filter(
        id=document_id,
        user=request.user
    ).first()

    if not document:
        return JsonResponse({
            "success": False,
            "message": "Document not found."
        }, status=404)

    pages = document.pages

    # ----------------------------
    # Pricing
    # ----------------------------

    bw_price = Decimal("5")
    color_price = Decimal("20")
    a3_charge = Decimal("10")
    double_discount = Decimal("1")

    price_per_page = color_price if color else bw_price

    subtotal = Decimal(pages * copies) * price_per_page

    paper_charge = Decimal("0")

    if paper_size == "A3":
        paper_charge = Decimal(pages * copies) * a3_charge

    color_charge = Decimal("0")

    if color:
        color_charge = Decimal(pages * copies) * (color_price - bw_price)

    discount = Decimal("0")

    if double_sided:
        discount = Decimal(pages * copies) * double_discount

    total = subtotal + paper_charge - discount

    # ----------------------------
    # Create Print Job
    # ----------------------------

    print_job = PrintJob.objects.create(
        user=request.user,
        document=document,
        copies=copies,
        paper_size=paper_size,
        color=color,
        double_sided=double_sided,
        status="pending"
    )

    # ----------------------------
    # Create Payment
    # ----------------------------

    payment = Payment.objects.create(
        print_job=print_job,
        subtotal=subtotal,
        paper_charge=paper_charge,
        color_charge=color_charge,
        discount=discount,
        amount=total,
        payment_method=payment_method,
        status="pending"
    )

    return JsonResponse({
        "success": True,
        "message": "Print job created successfully.",
        "print_job": {
            "id": print_job.id,
            "document": document.original_name,
            "copies": print_job.copies,
            "paper_size": print_job.paper_size,
            "color": print_job.color,
            "double_sided": print_job.double_sided,
            "status": print_job.status,
        },
        "payment": {
            "id": payment.id,
            "subtotal": payment.subtotal,
            "paper_charge": payment.paper_charge,
            "color_charge": payment.color_charge,
            "discount": payment.discount,
            "amount": payment.amount,
            "status": payment.status,
        }
    }, status=201)