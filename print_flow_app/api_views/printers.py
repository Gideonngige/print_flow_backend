# from .common_imports import *


# # ============================================================
# # LIST + CREATE PRINTERS
# # ============================================================

# @api_view(["GET", "POST"])
# @permission_classes([IsAuthenticated])
# def business_printers(request):

#     user = request.user

#     if user.role not in [
#         "business_admin",
#         "staff",
#     ]:
#         return Response({
#             "message":
#                 "You are not allowed to access printers."
#         }, status=403)

#     tenant = user.tenant

#     if not tenant:
#         return Response({
#             "message":
#                 "Your account is not linked to a business."
#         }, status=400)


#     # ========================================================
#     # GET
#     # ========================================================

#     if request.method == "GET":

#         printers = (
#             Printer.objects
#             .filter(
#                 tenant=tenant
#             )
#             .order_by(
#                 "-is_default",
#                 "name",
#             )
#         )

#         data = []

#         for printer in printers:

#             data.append({
#                 "id":
#                     printer.id,

#                 "name":
#                     printer.name,

#                 "system_name":
#                     printer.system_name,

#                 "connection_type":
#                     printer.connection_type,

#                 "ip_address":
#                     printer.ip_address,

#                 "port":
#                     printer.port,

#                 "status":
#                     printer.status,

#                 "is_default":
#                     printer.is_default,

#                 "is_active":
#                     printer.is_active,

#                 "created_at":
#                     printer.created_at,

#                 "updated_at":
#                     printer.updated_at,
#             })

#         return Response({
#             "success": True,
#             "count": len(data),
#             "printers": data,
#         })


#     # ========================================================
#     # POST
#     # ========================================================

#     if user.role != "business_admin":

#         return Response({
#             "message":
#                 "Only the business administrator "
#                 "can add printers."
#         }, status=403)


#     name = (
#         request.data
#         .get("name", "")
#         .strip()
#     )

#     system_name = (
#         request.data
#         .get("system_name", "")
#         .strip()
#     )

#     connection_type = (
#         request.data
#         .get(
#             "connection_type",
#             "network"
#         )
#         .strip()
#     )

#     ip_address = (
#         request.data
#         .get("ip_address", "")
#         .strip()
#     )

#     port = request.data.get(
#         "port",
#         631
#     )

#     is_default = request.data.get(
#         "is_default",
#         False
#     )


#     if not name:

#         return Response({
#             "message":
#                 "Printer name is required."
#         }, status=400)


#     if not system_name:

#         return Response({
#             "message":
#                 "System printer name is required."
#         }, status=400)


#     valid_connection_types = [
#         "network",
#         "usb",
#         "local",
#     ]


#     if (
#         connection_type not in
#         valid_connection_types
#     ):

#         return Response({
#             "message":
#                 "Invalid connection type."
#         }, status=400)


#     # Network printer should have IP
#     if (
#         connection_type == "network"
#         and not ip_address
#     ):

#         return Response({
#             "message":
#                 "IP address is required "
#                 "for a network printer."
#         }, status=400)


#     try:
#         port = int(port)

#     except (
#         ValueError,
#         TypeError,
#     ):

#         return Response({
#             "message":
#                 "Printer port must be a valid number."
#         }, status=400)


#     if port < 1 or port > 65535:

#         return Response({
#             "message":
#                 "Printer port is invalid."
#         }, status=400)


#     # Prevent duplicate CUPS/system printer
#     if Printer.objects.filter(
#         tenant=tenant,
#         system_name__iexact=
#             system_name
#     ).exists():

#         return Response({
#             "message":
#                 "This printer is already registered."
#         }, status=400)


#     with transaction.atomic():

#         # Only one default printer
#         if is_default:

#             Printer.objects.filter(
#                 tenant=tenant,
#                 is_default=True
#             ).update(
#                 is_default=False
#             )


#         printer = Printer.objects.create(
#             tenant=tenant,

#             name=name,

#             system_name=system_name,

#             connection_type=
#                 connection_type,

#             ip_address=
#                 ip_address or None,

#             port=port,

#             status="offline",

#             is_default=
#                 is_default,

#             is_active=True,
#         )


#     return Response({
#         "success": True,

#         "message":
#             "Printer added successfully.",

#         "printer": {
#             "id":
#                 printer.id,

#             "name":
#                 printer.name,

#             "system_name":
#                 printer.system_name,

#             "connection_type":
#                 printer.connection_type,

#             "ip_address":
#                 printer.ip_address,

#             "port":
#                 printer.port,

#             "status":
#                 printer.status,

#             "is_default":
#                 printer.is_default,

#             "is_active":
#                 printer.is_active,
#         }
#     }, status=201)


# # ============================================================
# # PRINTER DETAIL
# # ============================================================

# @api_view(["GET"])
# @permission_classes([IsAuthenticated])
# def business_printer_detail(
#     request,
#     printer_id
# ):

#     user = request.user

#     if user.role not in [
#         "business_admin",
#         "staff",
#     ]:

#         return Response({
#             "message":
#                 "You are not allowed "
#                 "to access this printer."
#         }, status=403)


#     tenant = user.tenant


#     printer = Printer.objects.filter(
#         id=printer_id,
#         tenant=tenant
#     ).first()


#     if not printer:

#         return Response({
#             "message":
#                 "Printer not found."
#         }, status=404)


#     return Response({
#         "success": True,

#         "printer": {
#             "id":
#                 printer.id,

#             "name":
#                 printer.name,

#             "system_name":
#                 printer.system_name,

#             "connection_type":
#                 printer.connection_type,

#             "ip_address":
#                 printer.ip_address,

#             "port":
#                 printer.port,

#             "status":
#                 printer.status,

#             "is_default":
#                 printer.is_default,

#             "is_active":
#                 printer.is_active,

#             "created_at":
#                 printer.created_at,

#             "updated_at":
#                 printer.updated_at,
#         }
#     })



from .common_imports import *
import secrets


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def business_printers(request):

    user = request.user

    if user.role not in [
        "business_admin",
        "staff",
    ]:
        return Response({
            "success": False,
            "message":
                "You are not allowed to access printers."
        }, status=403)

    tenant = user.tenant

    if not tenant:
        return Response({
            "success": False,
            "message":
                "Your account is not linked to a business."
        }, status=400)

    if request.method == "GET":

        printers = (
            Printer.objects
            .filter(
                tenant=tenant
            )
            .order_by(
                "-created_at"
            )
        )

        data = []

        for printer in printers:

            agent = (
                PrintAgent.objects
                .filter(
                    printer=printer,
                    tenant=tenant,
                    is_active=True
                )
                .first()
            )

            data.append({
                "id":
                    printer.id,

                "name":
                    printer.name,

                "local_printer_name":
                    printer.local_printer_name,

                "is_active":
                    printer.is_active,

                "created_at":
                    printer.created_at,

                "updated_at":
                    printer.updated_at,

                "agent": {
                    "id":
                        agent.id,

                    "name":
                        agent.name,

                    "machine_name":
                        agent.machine_name,

                    "last_seen":
                        agent.last_seen,
                }
                if agent
                else None,
            })

        return Response({
            "success": True,
            "printers": data,
        })


    if user.role != "business_admin":
        return Response({
            "success": False,
            "message":
                "Only the business administrator can add printers."
        }, status=403)

    name = (
        request.data
        .get(
            "name",
            ""
        )
        .strip()
    )

    if not name:
        return Response({
            "success": False,
            "message":
                "Printer name is required."
        }, status=400)

    printer = Printer.objects.create(
        tenant=tenant,
        name=name,
        is_active=True,
    )

    return Response({
        "success": True,
        "message":
            "Printer created successfully.",

        "printer": {
            "id":
                printer.id,

            "name":
                printer.name,

            "local_printer_name":
                printer.local_printer_name,

            "is_active":
                printer.is_active,
        }
    }, status=201)


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def business_printer_detail(
    request,
    printer_id
):

    user = request.user

    if user.role != "business_admin":
        return Response({
            "success": False,
            "message":
                "Only the business administrator can manage printers."
        }, status=403)

    tenant = user.tenant

    printer = (
        Printer.objects
        .filter(
            id=printer_id,
            tenant=tenant
        )
        .first()
    )

    if not printer:
        return Response({
            "success": False,
            "message":
                "Printer not found."
        }, status=404)


    if request.method == "DELETE":

        linked_agent_exists = (
            PrintAgent.objects
            .filter(
                printer=printer
            )
            .exists()
        )

        if linked_agent_exists:
            return Response({
                "success": False,
                "message":
                    "Disconnect the Print Agent before deleting this printer."
            }, status=400)

        printer.delete()

        return Response({
            "success": True,
            "message":
                "Printer deleted successfully."
        })


    name = request.data.get(
        "name",
        printer.name
    )

    is_active = request.data.get(
        "is_active",
        printer.is_active
    )

    if isinstance(name, str):
        name = name.strip()

    if not name:
        return Response({
            "success": False,
            "message":
                "Printer name is required."
        }, status=400)

    printer.name = name
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

            "local_printer_name":
                printer.local_printer_name,

            "is_active":
                printer.is_active,
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





# ============================================================
# BUSINESS PRINT AGENTS
# ============================================================

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def business_print_agents(request):

    user = request.user

    if user.role not in [
        "business_admin",
        "staff",
    ]:
        return Response({
            "success": False,
            "message":
                "You are not allowed to access Print Agents."
        }, status=403)

    tenant = user.tenant

    if not tenant:
        return Response({
            "success": False,
            "message":
                "Your account is not linked to a business."
        }, status=400)

    # ========================================================
    # GET
    # ========================================================

    if request.method == "GET":

        agents = (
            PrintAgent.objects
            .filter(
                tenant=tenant
            )
            .select_related(
                "printer"
            )
            .order_by(
                "-created_at"
            )
        )

        agents_data = []

        now = timezone.now()

        for agent in agents:

            discovered_count = (
                DiscoveredPrinter.objects
                .filter(
                    agent=agent
                )
                .count()
            )

            online = False

            if agent.last_seen:

                online = (
                    now -
                    agent.last_seen
                ).total_seconds() <= 90

            agents_data.append({
                "id":
                    agent.id,

                "name":
                    agent.name,

                "machine_name":
                    agent.machine_name,

                "is_active":
                    agent.is_active,

                "last_seen":
                    agent.last_seen,

                "online":
                    online,

                "created_at":
                    agent.created_at,

                "updated_at":
                    agent.updated_at,

                "discovered_printers_count":
                    discovered_count,

                "printer": {
                    "id":
                        agent.printer.id,

                    "name":
                        agent.printer.name,

                    "local_printer_name":
                        agent.printer.local_printer_name,

                    "is_active":
                        agent.printer.is_active,
                }
                if agent.printer
                else None,
            })

        return Response({
            "success": True,

            "count":
                len(
                    agents_data
                ),

            "agents":
                agents_data,
        })

    # ========================================================
    # CREATE
    # ========================================================

    if user.role != "business_admin":

        return Response({
            "success": False,
            "message":
                "Only the business administrator can create Print Agents."
        }, status=403)

    name = (
        str(
            request.data.get(
                "name",
                ""
            )
        )
        .strip()
    )

    if not name:

        return Response({
            "success": False,
            "message":
                "Print Agent name is required."
        }, status=400)

    if (
        PrintAgent.objects
        .filter(
            tenant=tenant,
            name__iexact=name
        )
        .exists()
    ):

        return Response({
            "success": False,
            "message":
                "A Print Agent with this name already exists."
        }, status=400)

    # Generate secure API key
    api_key = (
        secrets.token_urlsafe(
            48
        )
    )

    agent = (
        PrintAgent.objects
        .create(
            tenant=tenant,

            name=name,

            api_key=api_key,

            is_active=True,
        )
    )

    return Response({
        "success": True,

        "message":
            "Print Agent created successfully.",

        # IMPORTANT:
        # Return key only when agent is created.
        "api_key":
            api_key,

        "agent": {
            "id":
                agent.id,

            "name":
                agent.name,

            "machine_name":
                agent.machine_name,

            "is_active":
                agent.is_active,

            "created_at":
                agent.created_at,
        },

    }, status=201)


# ============================================================
# UPDATE / DELETE PRINT AGENT
# ============================================================

@api_view([
    "PATCH",
    "DELETE"
])
@permission_classes([IsAuthenticated])
def business_print_agent_detail(
    request,
    agent_id
):

    user = request.user

    if user.role != "business_admin":

        return Response({
            "success": False,
            "message":
                "Only the business administrator can manage Print Agents."
        }, status=403)

    tenant = user.tenant

    if not tenant:

        return Response({
            "success": False,
            "message":
                "Your account is not linked to a business."
        }, status=400)

    agent = (
        PrintAgent.objects
        .filter(
            id=agent_id,
            tenant=tenant
        )
        .first()
    )

    if not agent:

        return Response({
            "success": False,
            "message":
                "Print Agent not found."
        }, status=404)

    # ========================================================
    # DELETE
    # ========================================================

    if request.method == "DELETE":

        name = (
            agent.name
        )

        agent.delete()

        return Response({
            "success": True,

            "message":
                f"{name} deleted successfully."
        })

    # ========================================================
    # PATCH
    # ========================================================

    name = request.data.get(
        "name",
        agent.name
    )

    is_active = request.data.get(
        "is_active",
        agent.is_active
    )

    if isinstance(
        name,
        str
    ):
        name = (
            name.strip()
        )

    if not name:

        return Response({
            "success": False,
            "message":
                "Print Agent name is required."
        }, status=400)

    duplicate = (
        PrintAgent.objects
        .filter(
            tenant=tenant,
            name__iexact=name
        )
        .exclude(
            id=agent.id
        )
        .exists()
    )

    if duplicate:

        return Response({
            "success": False,
            "message":
                "Another Print Agent already uses this name."
        }, status=400)

    agent.name = (
        name
    )

    if isinstance(
        is_active,
        bool
    ):
        agent.is_active = (
            is_active
        )

    agent.save()

    return Response({
        "success": True,

        "message":
            "Print Agent updated successfully.",

        "agent": {
            "id":
                agent.id,

            "name":
                agent.name,

            "machine_name":
                agent.machine_name,

            "is_active":
                agent.is_active,

            "last_seen":
                agent.last_seen,
        }
    })


# ============================================================
# REGENERATE API KEY
# ============================================================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def business_regenerate_agent_key(
    request,
    agent_id
):

    user = request.user

    if user.role != "business_admin":

        return Response({
            "success": False,
            "message":
                "Only the business administrator can regenerate API keys."
        }, status=403)

    tenant = user.tenant

    agent = (
        PrintAgent.objects
        .filter(
            id=agent_id,
            tenant=tenant
        )
        .first()
    )

    if not agent:

        return Response({
            "success": False,
            "message":
                "Print Agent not found."
        }, status=404)

    api_key = (
        secrets.token_urlsafe(
            48
        )
    )

    agent.api_key = (
        api_key
    )

    agent.save(
        update_fields=[
            "api_key",
            "updated_at",
        ]
    )

    return Response({
        "success": True,

        "message":
            (
                "A new API key has been generated. "
                "The previous key will no longer work."
            ),

        "api_key":
            api_key,

        "agent": {
            "id":
                agent.id,

            "name":
                agent.name,
        }
    })


# ============================================================
# DISCONNECT AGENT FROM PRINTER
# ============================================================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def business_disconnect_agent_printer(
    request,
    agent_id
):

    user = request.user

    if user.role != "business_admin":

        return Response({
            "success": False,
            "message":
                "Only the business administrator can disconnect Print Agents."
        }, status=403)

    tenant = user.tenant

    agent = (
        PrintAgent.objects
        .filter(
            id=agent_id,
            tenant=tenant
        )
        .select_related(
            "printer"
        )
        .first()
    )

    if not agent:

        return Response({
            "success": False,
            "message":
                "Print Agent not found."
        }, status=404)

    printer = (
        agent.printer
    )

    agent.printer = None

    agent.save(
        update_fields=[
            "printer",
            "updated_at",
        ]
    )

    if printer:

        printer.local_printer_name = (
            None
        )

        printer.save(
            update_fields=[
                "local_printer_name",
                "updated_at",
            ]
        )

    return Response({
        "success": True,

        "message":
            "Print Agent disconnected from printer successfully."
    })