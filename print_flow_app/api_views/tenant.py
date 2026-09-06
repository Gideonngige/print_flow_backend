from .common_imports import *


# @api_view(["GET"])
# @permission_classes([AllowAny])
# def public_tenant_detail(
#     request,
#     slug
# ):
#     tenant = Tenant.objects.filter(
#         slug=slug,
#         is_active=True
#     ).first()

#     if not tenant:
#         return Response({
#             "message":
#                 "Printing business not found."
#         }, status=404)

#     return Response({
#         "success": True,

#         "tenant": {
#             "id":
#                 tenant.id,

#             "name":
#                 tenant.name,

#             "slug":
#                 tenant.slug,

#             "subdomain":
#                 tenant.subdomain,

#             "logo":
#                 tenant.logo,

#             "email":
#                 tenant.email,

#             "phone_number":
#                 tenant.phone_number,

#             "address":
#                 tenant.address,
#         }
#     })



@api_view(["GET"])
@permission_classes([AllowAny])
def public_tenant_detail(
    request,
    slug
):

    tenant = get_object_or_404(
        Tenant,
        slug=slug,
        is_active=True,
    )

    state = (
        get_subscription_state(
            tenant
        )
    )

    return Response(
        {
            "success": True,

            "tenant": {
                "id":
                    tenant.id,

                "name":
                    tenant.name,

                "slug":
                    tenant.slug,

                "email":
                    tenant.email,

                "phone":
                    tenant.phone,

                "address":
                    tenant.address,

                "logo":
                    tenant.logo.url
                    if tenant.logo
                    else None,
            },

            "subscription": {
                "has_subscription":
                    state[
                        "has_subscription"
                    ],

                "is_active":
                    state[
                        "is_active"
                    ],

                "is_expired":
                    state[
                        "is_expired"
                    ],
            },
        }
    )