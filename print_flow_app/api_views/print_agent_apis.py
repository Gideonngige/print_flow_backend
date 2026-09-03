from .common_imports import *

from django.utils import timezone
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response



from django.db import transaction
from django.utils import timezone
import datetime


STALE_AGENT_MINUTES = 5


def recover_stale_print_jobs():
    """
    Return abandoned printing jobs back to the queue.

    A job is considered stale when:
    - status == "printing"
    - it has an assigned PrintAgent
    - agent.last_seen is older than STALE_AGENT_MINUTES
      OR agent.last_seen is null
    """

    cutoff = (
        timezone.now()
        -
        datetime.timedelta(
            minutes=STALE_AGENT_MINUTES
        )
    )

    recovered_jobs = []

    with transaction.atomic():

        stale_jobs = (
            PrintJob.objects
            .select_for_update(
                skip_locked=True
            )
            .select_related(
                "print_agent",
                "printer",
                "document",
            )
            .filter(
                status="printing",
                print_agent__isnull=False,
            )
            .filter(
                Q(
                    print_agent__last_seen__lt=cutoff
                )
                |
                Q(
                    print_agent__last_seen__isnull=True
                )
            )
        )

        for job in stale_jobs:

            old_agent = (
                job.print_agent
            )

            old_printer = (
                job.printer
            )

            job.status = "queued"

            job.print_agent = None

            job.printer = None

            job.save(
                update_fields=[
                    "status",
                    "print_agent",
                    "printer",
                    "updated_at",
                ]
            )

            if job.document:

                job.document.status = (
                    "pending"
                )

                job.document.save(
                    update_fields=[
                        "status"
                    ]
                )

            recovered_jobs.append({
                "id":
                    job.id,

                "old_agent":
                    (
                        old_agent.name
                        if old_agent
                        else None
                    ),

                "old_printer":
                    (
                        old_printer.name
                        if old_printer
                        else None
                    ),
            })

    return recovered_jobs


# ============================================================
# PRINT AGENT AUTHENTICATION
# ============================================================

def authenticate_print_agent(request):
    """
    Expected header:

    X-Agent-Key: <agent-api-key>

    The API key determines:
    - agent
    - tenant
    - printer
    """

    api_key = (
        request.headers
        .get(
            "X-Agent-Key",
            ""
        )
        .strip()
    )

    if not api_key:
        return None, Response({
            "success": False,
            "message":
                "Print agent API key is required."
        }, status=401)

    agent = (
        PrintAgent.objects
        .select_related(
            "tenant",
            "printer",
        )
        .filter(
            api_key=api_key,
            is_active=True,
        )
        .first()
    )

    if not agent:
        return None, Response({
            "success": False,
            "message":
                "Invalid or inactive print agent."
        }, status=401)

    if not agent.tenant.is_active:
        return None, Response({
            "success": False,
            "message":
                "This printing business is currently inactive."
        }, status=403)

    # Update last seen
    agent.last_seen = (
        timezone.now()
    )

    agent.save(
        update_fields=[
            "last_seen",
            "updated_at",
        ]
    )

    return agent, None


# ============================================================
# AGENT CONFIGURATION
# ============================================================

@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def agent_config(request):

    agent, error_response = (
        authenticate_print_agent(
            request
        )
    )

    if error_response:
        return error_response

    printer = (
        agent.printer
    )

    return Response({
        "success": True,

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
        },

        "business": {
            "id":
                agent.tenant.id,

            "name":
                agent.tenant.name,

            "slug":
                agent.tenant.slug,

            "email":
                agent.tenant.email,

            "phone_number":
                agent.tenant.phone_number,
        },

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
        if printer
        else None,
    })


# ============================================================
# HEARTBEAT
# ============================================================

@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def agent_heartbeat(request):

    agent, error_response = (
        authenticate_print_agent(
            request
        )
    )

    if error_response:
        return error_response

    machine_name = (
        request.data.get(
            "machine_name"
        )
    )

    if machine_name:

        agent.machine_name = (
            str(
                machine_name
            )
            .strip()
        )

    agent.last_seen = (
        timezone.now()
    )

    agent.save(
        update_fields=[
            "machine_name",
            "last_seen",
            "updated_at",
        ]
    )

    return Response({
        "success": True,

        "message":
            "Heartbeat received.",

        "agent": {
            "id":
                agent.id,

            "last_seen":
                agent.last_seen,
        }
    })


# ============================================================
# GET NEXT PRINT JOB
# ============================================================


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def agent_next_job(request):

    agent, error_response = (
        authenticate_print_agent(
            request
        )
    )

    if error_response:
        return error_response

    # Recover abandoned jobs first
    try:
        recovered = (
            recover_stale_print_jobs()
        )

        if recovered:
            print(
                "RECOVERED STALE PRINT JOBS:",
                recovered
            )

    except Exception as error:
        print(
            "STALE JOB RECOVERY ERROR:",
            error
        )

    tenant = (
        agent.tenant
    )

    printer = (
        agent.printer
    )

    if not printer:

        return Response({
            "success": False,
            "message":
                "No printer is assigned to this Print Agent."
        }, status=400)

    if not printer.is_active:

        return Response({
            "success": False,
            "message":
                "The assigned printer is inactive."
        }, status=400)

    if not printer.local_printer_name:

        return Response({
            "success": False,
            "message":
                (
                    "The assigned printer is not mapped "
                    "to a local printer."
                )
        }, status=400)

    try:

        with transaction.atomic():

            job = (
                PrintJob.objects
                .select_for_update(
                    skip_locked=True
                )
                .select_related(
                    "document",
                    "user",
                    "tenant",
                )
                .filter(
                    tenant=tenant,
                    status="queued",
                    print_agent__isnull=True,
                )
                .order_by(
                    "created_at"
                )
                .first()
            )

            if not job:

                return Response({
                    "success": True,
                    "job_available":
                        False,
                    "message":
                        "No queued print jobs."
                })

            job.print_agent = (
                agent
            )

            job.printer = (
                printer
            )

            job.status = (
                "printing"
            )

            job.save(
                update_fields=[
                    "print_agent",
                    "printer",
                    "status",
                    "updated_at",
                ]
            )

            job.document.status = (
                "printing"
            )

            job.document.save(
                update_fields=[
                    "status"
                ]
            )

        return Response({
            "success": True,

            "job_available":
                True,

            "message":
                "Print job claimed successfully.",

            "print_job": {
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

                "created_at":
                    job.created_at,
            },

            "document": {
                "id":
                    job.document.id,

                "name":
                    job.document.original_name,

                "pages":
                    job.document.pages,

                "mime_type":
                    job.document.mime_type,

                "size":
                    job.document.size,

                "url":
                    job.document.cloudinary_url,
            },

            "customer": {
                "id":
                    job.user.id,

                "full_name":
                    job.user.full_name,

                "email":
                    job.user.email,

                "phone_number":
                    job.user.phone_number,
            },

            "printer": {
                "id":
                    printer.id,

                "name":
                    printer.name,

                "local_printer_name":
                    printer.local_printer_name,
            },

            "agent": {
                "id":
                    agent.id,

                "name":
                    agent.name,

                "machine_name":
                    agent.machine_name,
            },
        })

    except Exception as error:

        print(
            "AGENT NEXT JOB ERROR:",
            error
        )

        return Response({
            "success": False,
            "message":
                "Unable to claim the next print job."
        }, status=500)


# ============================================================
# START PRINTING
# ============================================================

@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def agent_start_printing(request):

    agent, error_response = (
        authenticate_print_agent(
            request
        )
    )

    if error_response:
        return error_response

    print_job_id = (
        request.data.get(
            "print_job_id"
        )
    )

    if not print_job_id:

        return Response({
            "success": False,
            "message":
                "Print job ID is required."
        }, status=400)

    job = (
        PrintJob.objects
        .select_related(
            "document"
        )
        .filter(
            id=print_job_id,
            tenant=agent.tenant,
        )
        .first()
    )

    if not job:

        return Response({
            "success": False,
            "message":
                "Print job not found."
        }, status=404)

    if job.status != "queued":

        return Response({
            "success": False,
            "message":
                f"Print job cannot start while status is {job.status}."
        }, status=400)

    job.status = (
        "printing"
    )

    job.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    job.document.status = (
        "printing"
    )

    job.document.save(
        update_fields=[
            "status"
        ]
    )

    return Response({
        "success": True,

        "message":
            "Printing started.",

        "print_job": {
            "id":
                job.id,

            "status":
                job.status,
        }
    })


# ============================================================
# COMPLETE PRINT JOB
# ============================================================

@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def agent_complete_job(request):

    agent, error_response = (
        authenticate_print_agent(
            request
        )
    )

    if error_response:
        return error_response


    print_job_id = (
        request.data.get(
            "print_job_id"
        )
    )


    if not print_job_id:

        return Response({
            "success": False,

            "message":
                "Print job ID is required."
        }, status=400)


    job = (
        PrintJob.objects
        .select_related(
            "document"
        )
        .filter(
            id=print_job_id,

            tenant=
                agent.tenant,

            print_agent=
                agent,
        )
        .first()
    )


    if not job:

        return Response({
            "success": False,

            "message":
                (
                    "Print job was not found or "
                    "is assigned to another agent."
                )
        }, status=404)


    if job.status != "printing":

        return Response({
            "success": False,

            "message":
                (
                    f"Print job cannot be completed "
                    f"while status is {job.status}."
                )
        }, status=400)


    job.status = (
        "printed"
    )

    job.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )


    job.document.status = (
        "printed"
    )

    job.document.save(
        update_fields=[
            "status"
        ]
    )


    return Response({
        "success": True,

        "message":
            "Print job completed successfully.",

        "print_job": {
            "id":
                job.id,

            "status":
                job.status,
        }
    })


# ============================================================
# FAIL PRINT JOB
# ============================================================

@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def agent_fail_job(request):

    agent, error_response = (
        authenticate_print_agent(
            request
        )
    )

    if error_response:
        return error_response


    print_job_id = (
        request.data.get(
            "print_job_id"
        )
    )

    reason = (
        str(
            request.data.get(
                "reason",
                ""
            )
        )
        .strip()
    )


    if not print_job_id:

        return Response({
            "success": False,

            "message":
                "Print job ID is required."
        }, status=400)


    job = (
        PrintJob.objects
        .select_related(
            "document"
        )
        .filter(
            id=print_job_id,

            tenant=
                agent.tenant,

            print_agent=
                agent,
        )
        .first()
    )


    if not job:

        return Response({
            "success": False,

            "message":
                (
                    "Print job was not found or "
                    "is assigned to another agent."
                )
        }, status=404)


    if job.status == "printed":

        return Response({
            "success": False,

            "message":
                "A completed print job cannot be marked as failed."
        }, status=400)


    job.status = (
        "failed"
    )

    job.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )


    job.document.status = (
        "failed"
    )

    job.document.save(
        update_fields=[
            "status"
        ]
    )


    return Response({
        "success": True,

        "message":
            "Print job marked as failed.",

        "reason":
            reason,

        "print_job": {
            "id":
                job.id,

            "status":
                job.status,
        }
    })



# ============================================================
# SYNC DISCOVERED PRINTERS
# ============================================================

@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def agent_sync_printers(request):

    agent, error_response = (
        authenticate_print_agent(
            request
        )
    )

    if error_response:
        return error_response

    printers = request.data.get(
        "printers",
        []
    )

    if not isinstance(
        printers,
        list
    ):
        return Response({
            "success": False,
            "message":
                "Printers must be a list."
        }, status=400)

    synced = []

    seen_names = []

    for printer_data in printers:

        system_name = (
            str(
                printer_data.get(
                    "system_name",
                    ""
                )
            )
            .strip()
        )

        if not system_name:
            continue

        seen_names.append(
            system_name
        )

        discovered, created = (
            DiscoveredPrinter.objects
            .update_or_create(
                agent=agent,
                system_name=system_name,

                defaults={
                    "tenant":
                        agent.tenant,

                    "display_name":
                        printer_data.get(
                            "name",
                            system_name
                        ),

                    "status":
                        printer_data.get(
                            "status",
                            ""
                        ),

                    "is_default":
                        bool(
                            printer_data.get(
                                "is_default",
                                False
                            )
                        ),

                    "last_seen":
                        timezone.now(),
                }
            )
        )

        synced.append({
            "id":
                discovered.id,

            "system_name":
                discovered.system_name,

            "display_name":
                discovered.display_name,

            "status":
                discovered.status,

            "is_default":
                discovered.is_default,

            "created":
                created,
        })

    # Optional:
    # remove printers no longer detected

    DiscoveredPrinter.objects.filter(
        agent=agent
    ).exclude(
        system_name__in=
            seen_names
    ).delete()

    return Response({
        "success": True,

        "message":
            "Printers synchronized successfully.",

        "count":
            len(
                synced
            ),

        "printers":
            synced,
    })


# ============================================================
# BUSINESS - LIST DISCOVERED PRINTERS
# ============================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def business_discovered_printers(request):

    user = request.user

    if user.role not in [
        "business_admin",
        "staff",
    ]:
        return Response({
            "success": False,
            "message":
                "You are not allowed to access this resource."
        }, status=403)

    tenant = (
        user.tenant
    )

    if not tenant:
        return Response({
            "success": False,
            "message":
                "Your account is not linked to a business."
        }, status=400)

    printers = (
        DiscoveredPrinter.objects
        .filter(
            tenant=tenant
        )
        .select_related(
            "agent"
        )
        .order_by(
            "display_name"
        )
    )

    data = []

    for printer in printers:

        data.append({
            "id":
                printer.id,

            "system_name":
                printer.system_name,

            "display_name":
                printer.display_name,

            "status":
                printer.status,

            "is_default":
                printer.is_default,

            "last_seen":
                printer.last_seen,

            "agent": {
                "id":
                    printer.agent.id,

                "name":
                    printer.agent.name,

                "machine_name":
                    printer.agent.machine_name,

                "last_seen":
                    printer.agent.last_seen,
            }
        })

    return Response({
        "success": True,

        "count":
            len(
                data
            ),

        "printers":
            data,
    })


# ============================================================
# BUSINESS - MAP LOCAL PRINTER
# ============================================================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def business_map_local_printer(
    request,
    printer_id
):

    user = (
        request.user
    )

    if user.role != "business_admin":

        return Response({
            "success": False,
            "message":
                "Only the business administrator can map printers."
        }, status=403)

    tenant = (
        user.tenant
    )

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
                "PrintFlow printer not found."
        }, status=404)

    discovered_printer_id = (
        request.data.get(
            "discovered_printer_id"
        )
    )

    discovered = (
        DiscoveredPrinter.objects
        .filter(
            id=discovered_printer_id,
            tenant=tenant
        )
        .select_related(
            "agent"
        )
        .first()
    )

    if not discovered:

        return Response({
            "success": False,
            "message":
                "Detected printer not found."
        }, status=404)

    printer.local_printer_name = (
        discovered.system_name
    )

    printer.save(
        update_fields=[
            "local_printer_name",
            "updated_at",
        ]
    )

    # Assign that printer to the detecting agent
    agent = (
        discovered.agent
    )

    agent.printer = (
        printer
    )

    agent.save(
        update_fields=[
            "printer",
            "updated_at",
        ]
    )

    return Response({
        "success": True,

        "message":
            "Printer connected successfully.",

        "printer": {
            "id":
                printer.id,

            "name":
                printer.name,

            "local_printer_name":
                printer.local_printer_name,
        },

        "agent": {
            "id":
                agent.id,

            "name":
                agent.name,
        }
    })




@api_view(["POST"])
@permission_classes([IsAuthenticated])
def recover_stale_jobs(request):

    user = request.user

    if user.role not in [
        "business_admin",
        "platform_admin",
    ]:
        return Response({
            "success": False,
            "message":
                "You are not allowed to recover print jobs."
        }, status=403)

    try:

        recovered = (
            recover_stale_print_jobs()
        )

        return Response({
            "success": True,

            "message":
                (
                    f"{len(recovered)} stale "
                    f"print job(s) recovered."
                ),

            "count":
                len(recovered),

            "jobs":
                recovered,
        })

    except Exception as error:

        return Response({
            "success": False,
            "message":
                str(error),
        }, status=500)