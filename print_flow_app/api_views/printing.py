from .common_imports import *
from .helper import *




@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def get_print_job(request):
    if not verify_agent(request):
        return Response({"message": "Unauthorized"}, status=401)

    try:

        job = (
            PrintJob.objects
            .filter(status="queued")
            .select_related("document", "user")
            .order_by("created_at")
            .first()
        )

        if not job:
            return Response({
                "success": False,
                "message": "No pending print jobs."
            })

        document = job.document

        return Response({

            "success": True,

            "print_job": {
                "id": job.id,
                "copies": job.copies,
                "paper_size": job.paper_size,
                "color": job.color,
                "double_sided": job.double_sided,
                "status": job.status,
            },

            "document": {
                "id": document.id,
                "name": document.original_name,
                "pages": document.pages,
                "url": document.cloudinary_url,
                "mime_type": document.mime_type,
            }

        })

    except Exception as e:

        return Response({
            "message": str(e)
        }, status=500)



@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def start_printing(request):
    if not verify_agent(request):
        return Response({"message": "Unauthorized"}, status=401)
    if not verify_agent(request):
        return Response({"message": "Unauthorized"}, status=401)

    try:

        print_job_id = request.data.get("print_job_id")

        job = PrintJob.objects.filter(id=print_job_id).first()

        if not job:
            return Response({
                "message": "Print job not found."
            }, status=404)

        job.status = "printing"
        job.save()

        job.document.status = "printing"
        job.document.save()

        return Response({
            "success": True,
            "message": "Printing started."
        })

    except Exception as e:

        return Response({
            "message": str(e)
        }, status=500)



@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def complete_print_job(request):
    if not verify_agent(request):
        return Response({"message": "Unauthorized"}, status=401)
    if not verify_agent(request):
        return Response({"message": "Unauthorized"}, status=401)

    try:

        print_job_id = request.data.get("print_job_id")

        job = PrintJob.objects.filter(id=print_job_id).first()

        if not job:
            return Response({
                "message": "Print job not found."
            }, status=404)

        job.status = "printed"
        job.save()

        job.document.status = "printed"
        job.document.save()

        return Response({

            "success": True,
            "message": "Document printed successfully."

        })

    except Exception as e:

        return Response({
            "message": str(e)
        }, status=500)



@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def failed_print_job(request):
    if not verify_agent(request):
        return Response({"message": "Unauthorized"}, status=401)
    if not verify_agent(request):
        print("Unauthorized")
        return Response({"message": "Unauthorized"}, status=401)

    try:

        print_job_id = request.data.get("print_job_id")

        reason = request.data.get("reason", "")

        job = PrintJob.objects.filter(id=print_job_id).first()

        if not job:
            return Response({
                "message": "Print job not found."
            }, status=404)

        job.status = "failed"
        job.save()

        return Response({

            "success": True,
            "message": "Print job marked as failed.",
            "reason": reason

        })

    except Exception as e:

        return Response({
            "message": str(e)
        }, status=500)


@api_view(["GET"])
@permission_classes([AllowAny])
def printer_status(request):

    queued = PrintJob.objects.filter(status="queued").count()
    printing = PrintJob.objects.filter(status="printing").count()
    printed = PrintJob.objects.filter(status="printed").count()
    failed = PrintJob.objects.filter(status="failed").count()

    return Response({

        "queued": queued,
        "printing": printing,
        "printed": printed,
        "failed": failed

    })




