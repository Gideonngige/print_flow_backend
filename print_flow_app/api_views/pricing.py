from .common_imports import *

from .serializers import PublicPlanSerializer


# ============================================================
# LIST + CREATE BUSINESS PRICING
# ============================================================

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def business_pricing(request):
    user = request.user

    if user.role not in [
        "business_admin",
        "staff",
    ]:
        return Response({
            "message":
                "You are not allowed to access pricing."
        }, status=403)

    tenant = user.tenant

    if not tenant:
        return Response({
            "message":
                "Your account is not linked to a business."
        }, status=400)

    # --------------------------------------------------------
    # GET
    # --------------------------------------------------------

    if request.method == "GET":

        pricing = (
            Pricing.objects
            .filter(
                tenant=tenant
            )
            .order_by(
                "paper_size",
                "print_type",
                "sides",
            )
        )

        data = []

        for item in pricing:
            data.append({
                "id": item.id,
                "paper_size": item.paper_size,
                "print_type": item.print_type,
                "sides": item.sides,
                "price_per_page": item.price_per_page,
                "minimum_charge": item.minimum_charge,
                "is_active": item.is_active,
                "created_at": item.created_at,
                "updated_at": item.updated_at,
            })

        return Response({
            "success": True,
            "pricing": data,
        })

    # --------------------------------------------------------
    # POST
    # --------------------------------------------------------

    if user.role != "business_admin":
        return Response({
            "message":
                "Only the business administrator "
                "can create pricing rules."
        }, status=403)

    paper_size = request.data.get(
        "paper_size"
    )

    print_type = request.data.get(
        "print_type"
    )

    sides = request.data.get(
        "sides"
    )

    price_per_page = request.data.get(
        "price_per_page"
    )

    minimum_charge = request.data.get(
        "minimum_charge",
        0
    )

    valid_paper_sizes = [
        "A4",
        "A3",
        "A5",
        "LETTER",
        "LEGAL",
    ]

    valid_print_types = [
        "black_white",
        "color",
    ]

    valid_sides = [
        "single",
        "double",
    ]

    if paper_size not in valid_paper_sizes:
        return Response({
            "message":
                "Invalid paper size."
        }, status=400)

    if print_type not in valid_print_types:
        return Response({
            "message":
                "Invalid print type."
        }, status=400)

    if sides not in valid_sides:
        return Response({
            "message":
                "Invalid printing side."
        }, status=400)

    try:
        price_per_page = Decimal(
            str(price_per_page)
        )

        minimum_charge = Decimal(
            str(minimum_charge)
        )

    except (
        InvalidOperation,
        TypeError,
        ValueError,
    ):
        return Response({
            "message":
                "Pricing values must be valid numbers."
        }, status=400)

    if price_per_page < 0:
        return Response({
            "message":
                "Price per page cannot be negative."
        }, status=400)

    if minimum_charge < 0:
        return Response({
            "message":
                "Minimum charge cannot be negative."
        }, status=400)

    exists = Pricing.objects.filter(
        tenant=tenant,
        paper_size=paper_size,
        print_type=print_type,
        sides=sides,
    ).exists()

    if exists:
        return Response({
            "message":
                "A pricing rule already exists "
                "for this combination."
        }, status=400)

    pricing = Pricing.objects.create(
        tenant=tenant,
        paper_size=paper_size,
        print_type=print_type,
        sides=sides,
        price_per_page=price_per_page,
        minimum_charge=minimum_charge,
        is_active=True,
    )

    return Response({
        "success": True,
        "message":
            "Pricing rule created successfully.",

        "pricing": {
            "id": pricing.id,
            "paper_size": pricing.paper_size,
            "print_type": pricing.print_type,
            "sides": pricing.sides,
            "price_per_page": pricing.price_per_page,
            "minimum_charge": pricing.minimum_charge,
            "is_active": pricing.is_active,
        }
    }, status=201)


# ============================================================
# UPDATE BUSINESS PRICING
# ============================================================

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_business_pricing(
    request,
    pricing_id
):
    user = request.user

    if user.role != "business_admin":
        return Response({
            "message":
                "Only the business administrator "
                "can update pricing."
        }, status=403)

    tenant = user.tenant

    pricing = Pricing.objects.filter(
        id=pricing_id,
        tenant=tenant
    ).first()

    if not pricing:
        return Response({
            "message":
                "Pricing rule not found."
        }, status=404)

    price_per_page = request.data.get(
        "price_per_page",
        pricing.price_per_page
    )

    minimum_charge = request.data.get(
        "minimum_charge",
        pricing.minimum_charge
    )

    is_active = request.data.get(
        "is_active",
        pricing.is_active
    )

    try:
        price_per_page = Decimal(
            str(price_per_page)
        )

        minimum_charge = Decimal(
            str(minimum_charge)
        )

    except (
        InvalidOperation,
        TypeError,
        ValueError,
    ):
        return Response({
            "message":
                "Pricing values must be valid numbers."
        }, status=400)

    if price_per_page < 0:
        return Response({
            "message":
                "Price per page cannot be negative."
        }, status=400)

    if minimum_charge < 0:
        return Response({
            "message":
                "Minimum charge cannot be negative."
        }, status=400)

    if not isinstance(
        is_active,
        bool
    ):
        return Response({
            "message":
                "is_active must be true or false."
        }, status=400)

    pricing.price_per_page = price_per_page
    pricing.minimum_charge = minimum_charge
    pricing.is_active = is_active

    pricing.save()

    return Response({
        "success": True,
        "message":
            "Pricing rule updated successfully.",

        "pricing": {
            "id": pricing.id,
            "paper_size": pricing.paper_size,
            "print_type": pricing.print_type,
            "sides": pricing.sides,
            "price_per_page": pricing.price_per_page,
            "minimum_charge": pricing.minimum_charge,
            "is_active": pricing.is_active,
        }
    })


# ============================================================
# DELETE BUSINESS PRICING
# ============================================================

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_business_pricing(
    request,
    pricing_id
):
    user = request.user

    if user.role != "business_admin":
        return Response({
            "message":
                "Only the business administrator "
                "can delete pricing rules."
        }, status=403)

    tenant = user.tenant

    pricing = Pricing.objects.filter(
        id=pricing_id,
        tenant=tenant
    ).first()

    if not pricing:
        return Response({
            "message":
                "Pricing rule not found."
        }, status=404)

    pricing.delete()

    return Response({
        "success": True,
        "message":
            "Pricing rule deleted successfully."
    })




@api_view(["GET"])
@permission_classes([AllowAny])
def public_plans(request):
    """
    Public endpoint used by the pricing page.

    GET /api/v1/public/plans/
    """

    try:
        plans = (
            Plan.objects
            .filter(is_active=True)
            .order_by(
                "monthly_price",
                "id"
            )
        )

        serializer = PublicPlanSerializer(
            plans,
            many=True
        )

        return Response(
            {
                "success": True,
                "plans": serializer.data,
            },
            status=status.HTTP_200_OK
        )

    except Exception as error:
        return Response(
            {
                "success": False,
                "message": "Unable to load subscription plans.",
                "error": str(error),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )