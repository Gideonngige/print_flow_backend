from .common_imports import *
from .permissions import IsAdminUserRole

@api_view(["POST"])
@permission_classes([AllowAny])
def send_message(request):
    try:
        name = str(
            request.data.get("name", "")
        ).strip()

        email = str(
            request.data.get("email", "")
        ).strip().lower()

        phone_number = str(
            request.data.get("phone_number", "")
        ).strip()

        subject = str(
            request.data.get(
                "subject",
                "General Enquiry",
            )
        ).strip()

        message_text = str(
            request.data.get("message", "")
        ).strip()

        if not name:
            return Response({
                "success": False,
                "message": "Your name is required.",
            }, status=400)

        if not email:
            return Response({
                "success": False,
                "message": "Your email address is required.",
            }, status=400)

        try:
            validate_email(email)
        except ValidationError:
            return Response({
                "success": False,
                "message": "Enter a valid email address.",
            }, status=400)

        if not message_text:
            return Response({
                "success": False,
                "message": "Your message is required.",
            }, status=400)

        if len(message_text) < 10:
            return Response({
                "success": False,
                "message": (
                    "Your message must contain at "
                    "least 10 characters."
                ),
            }, status=400)

        contact_message = Message.objects.create(
            name=name,
            email=email,
            phone_number=phone_number or None,
            subject=subject or "General Enquiry",
            message=message_text,
            status="unread",
        )

        return Response({
            "success": True,
            "message": (
                "Your message has been sent successfully. "
                "Our team will contact you shortly."
            ),
            "contact_message": {
                "id": contact_message.id,
                "name": contact_message.name,
                "email": contact_message.email,
                "subject": contact_message.subject,
                "status": contact_message.status,
                "created_at": contact_message.created_at,
            },
        }, status=201)

    except Exception as error:
        print("SEND MESSAGE ERROR:", error)

        return Response({
            "success": False,
            "message": "Unable to send your message.",
        }, status=500)



@api_view(["GET"])
@permission_classes([IsAdminUserRole])
def admin_messages(request):
    try:
        search = request.GET.get(
            "search",
            "",
        ).strip()

        message_status = request.GET.get(
            "status",
            "",
        ).strip()

        messages = Message.objects.all().order_by(
            "-created_at"
        )

        if search:
            messages = messages.filter(
                Q(name__icontains=search)
                | Q(email__icontains=search)
                | Q(subject__icontains=search)
                | Q(message__icontains=search)
                | Q(phone_number__icontains=search)
            )

        if message_status:
            messages = messages.filter(
                status=message_status
            )

        messages_data = []

        for contact_message in messages:
            messages_data.append({
                "id": contact_message.id,
                "name": contact_message.name,
                "email": contact_message.email,
                "phone_number": (
                    contact_message.phone_number
                ),
                "subject": contact_message.subject,
                "message": contact_message.message,
                "status": contact_message.status,
                "admin_notes": (
                    contact_message.admin_notes
                ),
                "created_at": contact_message.created_at,
                "updated_at": contact_message.updated_at,
                "replied_at": contact_message.replied_at,
            })

        statistics = {
            "total": Message.objects.count(),
            "unread": Message.objects.filter(
                status="unread"
            ).count(),
            "read": Message.objects.filter(
                status="read"
            ).count(),
            "replied": Message.objects.filter(
                status="replied"
            ).count(),
            "closed": Message.objects.filter(
                status="closed"
            ).count(),
        }

        return Response({
            "success": True,
            "count": len(messages_data),
            "statistics": statistics,
            "messages": messages_data,
        })

    except Exception as error:
        return Response({
            "success": False,
            "message": str(error),
        }, status=500)



@api_view(["PATCH"])
@permission_classes([IsAdminUserRole])
def update_message_status(request, message_id):
    try:
        contact_message = Message.objects.filter(
            id=message_id
        ).first()

        if not contact_message:
            return Response({
                "success": False,
                "message": "Message not found.",
            }, status=404)

        new_status = request.data.get("status")

        allowed_statuses = [
            "unread",
            "read",
            "replied",
            "closed",
        ]

        if new_status not in allowed_statuses:
            return Response({
                "success": False,
                "message": "Invalid message status.",
            }, status=400)

        admin_notes = request.data.get(
            "admin_notes"
        )

        contact_message.status = new_status

        if admin_notes is not None:
            contact_message.admin_notes = (
                str(admin_notes).strip()
            )

        if new_status == "replied":
            contact_message.replied_at = (
                timezone.now()
            )

        contact_message.save()

        return Response({
            "success": True,
            "message": "Message updated successfully.",
            "contact_message": {
                "id": contact_message.id,
                "status": contact_message.status,
                "admin_notes": (
                    contact_message.admin_notes
                ),
                "replied_at": (
                    contact_message.replied_at
                ),
            },
        })

    except Exception as error:
        return Response({
            "success": False,
            "message": str(error),
        }, status=500)



@api_view(["DELETE"])
@permission_classes([IsAdminUserRole])
def delete_message(request, message_id):
    try:
        contact_message = Message.objects.filter(
            id=message_id
        ).first()

        if not contact_message:
            return Response({
                "success": False,
                "message": "Message not found.",
            }, status=404)

        contact_message.delete()

        return Response({
            "success": True,
            "message": "Message deleted successfully.",
        })

    except Exception as error:
        return Response({
            "success": False,
            "message": str(error),
        }, status=500)