from .common_imports import *


# ============================================================
# LIST + CREATE PRINTERS
# ============================================================

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def business_printers(request):

    user = request.user

    if user.role not in [
        "business_admin",
        "staff",
    ]:
        return Response({
            "message":
                "You are not allowed to access printers."
        }, status=403)

    tenant = user.tenant

    if not tenant:
        return Response({
            "message":
                "Your account is not linked to a business."
        }, status=400)


    # ========================================================
    # GET
    # ========================================================

    if request.method == "GET":

        printers = (
            Printer.objects
            .filter(
                tenant=tenant
            )
            .order_by(
                "-is_default",
                "name",
            )
        )

        data = []

        for printer in printers:

            data.append({
                "id":
                    printer.id,

                "name":
                    printer.name,

                "system_name":
                    printer.system_name,

                "connection_type":
                    printer.connection_type,

                "ip_address":
                    printer.ip_address,

                "port":
                    printer.port,

                "status":
                    printer.status,

                "is_default":
                    printer.is_default,

                "is_active":
                    printer.is_active,

                "created_at":
                    printer.created_at,

                "updated_at":
                    printer.updated_at,
            })

        return Response({
            "success": True,
            "count": len(data),
            "printers": data,
        })


    # ========================================================
    # POST
    # ========================================================

    if user.role != "business_admin":

        return Response({
            "message":
                "Only the business administrator "
                "can add printers."
        }, status=403)


    name = (
        request.data
        .get("name", "")
        .strip()
    )

    system_name = (
        request.data
        .get("system_name", "")
        .strip()
    )

    connection_type = (
        request.data
        .get(
            "connection_type",
            "network"
        )
        .strip()
    )

    ip_address = (
        request.data
        .get("ip_address", "")
        .strip()
    )

    port = request.data.get(
        "port",
        631
    )

    is_default = request.data.get(
        "is_default",
        False
    )


    if not name:

        return Response({
            "message":
                "Printer name is required."
        }, status=400)


    if not system_name:

        return Response({
            "message":
                "System printer name is required."
        }, status=400)


    valid_connection_types = [
        "network",
        "usb",
        "local",
    ]


    if (
        connection_type not in
        valid_connection_types
    ):

        return Response({
            "message":
                "Invalid connection type."
        }, status=400)


    # Network printer should have IP
    if (
        connection_type == "network"
        and not ip_address
    ):

        return Response({
            "message":
                "IP address is required "
                "for a network printer."
        }, status=400)


    try:
        port = int(port)

    except (
        ValueError,
        TypeError,
    ):

        return Response({
            "message":
                "Printer port must be a valid number."
        }, status=400)


    if port < 1 or port > 65535:

        return Response({
            "message":
                "Printer port is invalid."
        }, status=400)


    # Prevent duplicate CUPS/system printer
    if Printer.objects.filter(
        tenant=tenant,
        system_name__iexact=
            system_name
    ).exists():

        return Response({
            "message":
                "This printer is already registered."
        }, status=400)


    with transaction.atomic():

        # Only one default printer
        if is_default:

            Printer.objects.filter(
                tenant=tenant,
                is_default=True
            ).update(
                is_default=False
            )


        printer = Printer.objects.create(
            tenant=tenant,

            name=name,

            system_name=system_name,

            connection_type=
                connection_type,

            ip_address=
                ip_address or None,

            port=port,

            status="offline",

            is_default=
                is_default,

            is_active=True,
        )


    return Response({
        "success": True,

        "message":
            "Printer added successfully.",

        "printer": {
            "id":
                printer.id,

            "name":
                printer.name,

            "system_name":
                printer.system_name,

            "connection_type":
                printer.connection_type,

            "ip_address":
                printer.ip_address,

            "port":
                printer.port,

            "status":
                printer.status,

            "is_default":
                printer.is_default,

            "is_active":
                printer.is_active,
        }
    }, status=201)


# ============================================================
# PRINTER DETAIL
# ============================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def business_printer_detail(
    request,
    printer_id
):

    user = request.user

    if user.role not in [
        "business_admin",
        "staff",
    ]:

        return Response({
            "message":
                "You are not allowed "
                "to access this printer."
        }, status=403)


    tenant = user.tenant


    printer = Printer.objects.filter(
        id=printer_id,
        tenant=tenant
    ).first()


    if not printer:

        return Response({
            "message":
                "Printer not found."
        }, status=404)


    return Response({
        "success": True,

        "printer": {
            "id":
                printer.id,

            "name":
                printer.name,

            "system_name":
                printer.system_name,

            "connection_type":
                printer.connection_type,

            "ip_address":
                printer.ip_address,

            "port":
                printer.port,

            "status":
                printer.status,

            "is_default":
                printer.is_default,

            "is_active":
                printer.is_active,

            "created_at":
                printer.created_at,

            "updated_at":
                printer.updated_at,
        }
    })


# ============================================================
# UPDATE PRINTER
# ============================================================

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_business_printer(
    request,
    printer_id
):

    user = request.user

    if user.role != "business_admin":

        return Response({
            "message":
                "Only the business administrator "
                "can update printers."
        }, status=403)


    tenant = user.tenant


    printer = Printer.objects.filter(
        id=printer_id,
        tenant=tenant
    ).first()


    if not printer:

        return Response({
            "message":
                "Printer not found."
        }, status=404)


    name = request.data.get(
        "name",
        printer.name
    )

    system_name = request.data.get(
        "system_name",
        printer.system_name
    )

    connection_type = request.data.get(
        "connection_type",
        printer.connection_type
    )

    ip_address = request.data.get(
        "ip_address",
        printer.ip_address
    )

    port = request.data.get(
        "port",
        printer.port
    )

    is_default = request.data.get(
        "is_default",
        printer.is_default
    )

    is_active = request.data.get(
        "is_active",
        printer.is_active
    )


    valid_connection_types = [
        "network",
        "usb",
        "local",
    ]


    if (
        connection_type not in
        valid_connection_types
    ):

        return Response({
            "message":
                "Invalid connection type."
        }, status=400)


    try:
        port = int(port)

    except (
        TypeError,
        ValueError,
    ):

        return Response({
            "message":
                "Printer port must be valid."
        }, status=400)


    if (
        connection_type == "network"
        and not ip_address
    ):

        return Response({
            "message":
                "IP address is required "
                "for network printers."
        }, status=400)


    duplicate = (
        Printer.objects
        .filter(
            tenant=tenant,
            system_name__iexact=
                system_name
        )
        .exclude(
            id=printer.id
        )
        .exists()
    )


    if duplicate:

        return Response({
            "message":
                "Another printer already uses "
                "this system name."
        }, status=400)


    with transaction.atomic():

        if is_default:

            Printer.objects.filter(
                tenant=tenant,
                is_default=True
            ).exclude(
                id=printer.id
            ).update(
                is_default=False
            )


        printer.name = name
        printer.system_name = system_name
        printer.connection_type = (
            connection_type
        )
        printer.ip_address = (
            ip_address or None
        )
        printer.port = port
        printer.is_default = is_default
        printer.is_active = is_active

        printer.save()


    return Response({
        "success": True,

        "message":
            "Printer updated successfully.",

        "printer": {
            "id":
                printer.id,

            "name":
                printer.name,

            "system_name":
                printer.system_name,

            "connection_type":
                printer.connection_type,

            "ip_address":
                printer.ip_address,

            "port":
                printer.port,

            "status":
                printer.status,

            "is_default":
                printer.is_default,

            "is_active":
                printer.is_active,
        }
    })


# ============================================================
# SET DEFAULT PRINTER
# ============================================================

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def set_default_printer(
    request,
    printer_id
):

    user = request.user

    if user.role != "business_admin":

        return Response({
            "message":
                "Only the business administrator "
                "can change the default printer."
        }, status=403)


    tenant = user.tenant


    printer = Printer.objects.filter(
        id=printer_id,
        tenant=tenant,
        is_active=True
    ).first()


    if not printer:

        return Response({
            "message":
                "Printer not found."
        }, status=404)


    with transaction.atomic():

        Printer.objects.filter(
            tenant=tenant,
            is_default=True
        ).update(
            is_default=False
        )


        printer.is_default = True

        printer.save(
            update_fields=[
                "is_default",
                "updated_at",
            ]
        )


    return Response({
        "success": True,

        "message":
            f"{printer.name} is now "
            "the default printer."
    })


# ============================================================
# DELETE PRINTER
# ============================================================

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_business_printer(
    request,
    printer_id
):

    user = request.user

    if user.role != "business_admin":

        return Response({
            "message":
                "Only the business administrator "
                "can delete printers."
        }, status=403)


    tenant = user.tenant


    printer = Printer.objects.filter(
        id=printer_id,
        tenant=tenant
    ).first()


    if not printer:

        return Response({
            "message":
                "Printer not found."
        }, status=404)


    if printer.is_default:

        return Response({
            "message":
                "You cannot delete the default printer. "
                "Select another default printer first."
        }, status=400)


    printer.delete()


    return Response({
        "success": True,

        "message":
            "Printer deleted successfully."
    })