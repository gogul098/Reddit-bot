import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from celery.result import AsyncResult
from .schemas import AnalyzeRequest
from .tasks import master_text_pipeline_task, video_master_task
from pydantic import ValidationError

@csrf_exempt
def analyze_view(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            # Pydantic validation
            payload = AnalyzeRequest(**data)
            
            # Dispatch the Master Pipeline Task (Handles Cleaning -> Clustering -> Analysis)
            task = master_text_pipeline_task.delay(
                payload.title,
                [c.model_dump() for c in payload.comments]
            )
            
            return JsonResponse({
                "task_id": task.id
            }, status=202)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except ValidationError as e:
            return JsonResponse({"error": "Validation Error", "details": e.errors()}, status=400)
            
    return JsonResponse({"error": "Method not allowed"}, status=405)

def status_view(request, task_id):
    if request.method == "GET":
        task_result = AsyncResult(task_id)
        result = {
            "task_id": task_id,
            "status": task_result.status,
            "result": str(task_result.result) if task_result.ready() else None
        }
        return JsonResponse(result)
        
    return JsonResponse({"error": "Method not allowed"}, status=405)
