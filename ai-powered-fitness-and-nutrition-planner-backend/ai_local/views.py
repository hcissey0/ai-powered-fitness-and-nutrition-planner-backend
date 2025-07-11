from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from .services import get_local_model

# Optional: You can add views here for AI model management
# For example, a view to check model status, reload model, etc.

@require_http_methods(["GET"])
def model_status(request):
    """
    Check the status of the local AI model
    """
    try:
        model = get_local_model()
        status = {
            'model_loaded': model.model is not None,
            'model_path': model.model_path,
            'status': 'ready' if model.model else 'fallback_only'
        }
        return JsonResponse(status)
    except Exception as e:
        return JsonResponse({
            'model_loaded': False,
            'error': str(e),
            'status': 'error'
        }, status=500)
