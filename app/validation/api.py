"""JSON API. Every endpoint except health requires the shared key in the X-API-Key header."""
import json
from functools import wraps

from django.conf import settings
from django.http import JsonResponse
from django.utils.crypto import constant_time_compare
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import ValidationRun
from .rules import validate_records


def _error(message: str, status: int) -> JsonResponse:
    return JsonResponse({"error": message}, status=status)


def require_api_key(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        provided = request.headers.get("X-API-Key", "")
        if not constant_time_compare(provided, settings.VALIDATOR_API_KEY):
            return _error("Invalid or missing API key.", 401)
        return view(request, *args, **kwargs)

    return wrapper


@require_GET
def health(request):
    return JsonResponse({"status": "ok"})


@csrf_exempt
@require_POST
@require_api_key
def validate(request):
    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return _error("Request body must be valid JSON.", 400)

    records = payload.get("records") if isinstance(payload, dict) else None
    if not isinstance(records, list) or not all(isinstance(r, dict) for r in records):
        return _error('"records" must be a list of objects.', 400)
    if not records:
        return _error('"records" must not be empty.', 400)
    if len(records) > settings.VALIDATOR_MAX_ROWS:
        return _error(f'"records" exceeds the limit of {settings.VALIDATOR_MAX_ROWS}.', 400)

    name = payload.get("name", "")
    run = ValidationRun.record(
        validate_records(records),
        source=ValidationRun.Source.API,
        filename=name if isinstance(name, str) else "",
    )
    return JsonResponse(run.to_dict(include_errors=True), status=201)


@require_GET
@require_api_key
def run_list(request):
    runs = ValidationRun.objects.all()[:50]
    return JsonResponse({"runs": [run.to_dict() for run in runs]})


@require_GET
@require_api_key
def run_detail(request, pk):
    try:
        run = ValidationRun.objects.get(pk=pk)
    except ValidationRun.DoesNotExist:
        return _error("Run not found.", 404)
    return JsonResponse(run.to_dict(include_errors=True))
