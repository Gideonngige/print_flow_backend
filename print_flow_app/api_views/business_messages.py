from .common_imports import *


# ============================================================
# LIST BUSINESS MESSAGES
# ============================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def business_messages(request):

    user = request.user

    if user.role not in [
        "business_admin",
        "staff",
    ]:
        return Response({
            "message":
                "You are not allowed to access messages."
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

    messages = (
        Message.objects
        .filter(
            tenant=tenant
        )
        .select_related(
            "user"
        )
        .order_by(
            "-created_at"
        )
    )

    # --------------------------------------------------------
    # Search
    # --------------------------------------------------------

    if search:
        messages = messages.filter(
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
                subject__icontains=
                    search
            )
            |
            Q(
                message__icontains=
                    search
            )
        )

    # --------------------------------------------------------
    # Status filter
    # --------------------------------------------------------

    valid_statuses = [
        "unread",
        "read",
        "replied",
        "closed",
    ]

    if (
        status_filter and
        status_filter in valid_statuses
    ):
        messages = messages.filter(
            status=status_filter
        )

    data = []

    for message in messages:

        data.append({
            "id":
                message.id,

            "name":
                message.name,

            "email":
                message.email,

            "phone_number":
                message.phone_number,

            "subject":
                message.subject,

            "message":
                message.message,

            "status":
                message.status,

            "admin_notes":
                message.admin_notes,

            "created_at":
                message.created_at,

            "updated_at":
                message.updated_at,

            "replied_at":
                message.replied_at,

            "user": {
                "id":
                    message.user.id,

                "full_name":
                    message.user.full_name,

                "email":
                    message.user.email,
            }
            if message.user
            else None,
        })

    # --------------------------------------------------------
    # Stats
    # --------------------------------------------------------

    base = Message.objects.filter(
        tenant=tenant
    )

    stats = {
        "total":
            base.count(),

        "unread":
            base.filter(
                status="unread"
            ).count(),

        "read":
            base.filter(
                status="read"
            ).count(),

        "replied":
            base.filter(
                status="replied"
            ).count(),

        "closed":
            base.filter(
                status="closed"
            ).count(),
    }

    return Response({
        "success": True,
        "count": len(data),
        "stats": stats,
        "messages": data,
    })


# ============================================================
# MESSAGE DETAIL
# ============================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def business_message_detail(
    request,
    message_id
):

    user = request.user

    if user.role not in [
        "business_admin",
        "staff",
    ]:
        return Response({
            "message":
                "You are not allowed to access this message."
        }, status=403)

    tenant = user.tenant

    message = (
        Message.objects
        .filter(
            id=message_id,
            tenant=tenant
        )
        .select_related(
            "user"
        )
        .first()
    )

    if not message:
        return Response({
            "message":
                "Message not found."
        }, status=404)

    # Automatically mark unread message as read
    if message.status == "unread":

        message.status = "read"

        message.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

    return Response({
        "success": True,

        "message_data": {
            "id":
                message.id,

            "name":
                message.name,

            "email":
                message.email,

            "phone_number":
                message.phone_number,

            "subject":
                message.subject,

            "message":
                message.message,

            "status":
                message.status,

            "admin_notes":
                message.admin_notes,

            "created_at":
                message.created_at,

            "updated_at":
                message.updated_at,

            "replied_at":
                message.replied_at,

            "user": {
                "id":
                    message.user.id,

                "full_name":
                    message.user.full_name,

                "email":
                    message.user.email,
            }
            if message.user
            else None,
        }
    })


# ============================================================
# UPDATE MESSAGE
# ============================================================

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_business_message(
    request,
    message_id
):

    user = request.user

    if user.role not in [
        "business_admin",
        "staff",
    ]:
        return Response({
            "message":
                "You are not allowed to update this message."
        }, status=403)

    tenant = user.tenant

    message = Message.objects.filter(
        id=message_id,
        tenant=tenant
    ).first()

    if not message:
        return Response({
            "message":
                "Message not found."
        }, status=404)

    status_value = request.data.get(
        "status",
        message.status
    )

    admin_notes = request.data.get(
        "admin_notes",
        message.admin_notes
    )

    valid_statuses = [
        "unread",
        "read",
        "replied",
        "closed",
    ]

    if status_value not in valid_statuses:

        return Response({
            "message":
                "Invalid message status."
        }, status=400)

    message.status = status_value
    message.admin_notes = admin_notes

    if status_value == "replied":

        if not message.replied_at:
            message.replied_at = (
                timezone.now()
            )

    elif status_value != "replied":

        # Keep replied_at if it was already replied.
        # Do not erase history.
        pass

    message.save()

    return Response({
        "success": True,

        "message":
            "Message updated successfully.",

        "message_data": {
            "id":
                message.id,

            "status":
                message.status,

            "admin_notes":
                message.admin_notes,

            "replied_at":
                message.replied_at,
        }
    })


# ============================================================
# DELETE MESSAGE
# ============================================================

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_business_message(
    request,
    message_id
):

    user = request.user

    if user.role != "business_admin":

        return Response({
            "message":
                "Only the business administrator "
                "can delete messages."
        }, status=403)

    tenant = user.tenant

    message = Message.objects.filter(
        id=message_id,
        tenant=tenant
    ).first()

    if not message:

        return Response({
            "message":
                "Message not found."
        }, status=404)

    message.delete()

    return Response({
        "success": True,

        "message":
            "Message deleted successfully."
    })