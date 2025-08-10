import uuid
from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError, NotAuthenticated, PermissionDenied, Throttled, NotFound, ErrorDetail

def _flatten(prefix, data, out):
    if isinstance(data, dict):
        for k, v in data.items():
            _flatten(f"{prefix}.{k}" if prefix else k, v, out)
    elif isinstance(data, list):
        for v in data:
            _flatten(prefix, v, out)
    else:
        # data est souvent ErrorDetail(message, code)
        if isinstance(data, ErrorDetail):
            out.append({"field": prefix, "code": data.code or "INVALID", "params": {}})
        else:
            out.append({"field": prefix, "code": "INVALID", "params": {}})

def drf_exception_handler(exc, context):
    resp = exception_handler(exc, context)
    if resp is None:
        return resp

    # Content-Type correct pour un problème
    resp['Content-Type'] = 'application/problem+json'

    trace_id = str(uuid.uuid4())

    if isinstance(exc, ValidationError):
        fields = []
        _flatten("", resp.data, fields)
        resp.data = {
            "type": "https://api.conversa.app/problems/validation-error",
            "title": "Validation Error",
            "status": resp.status_code,
            "detail": "Some fields are invalid.",
            "code": "VALIDATION_ERROR",
            "params": {},
            "fields": fields,
            "trace_id": trace_id,
        }
        return resp

    mapping = {
        NotAuthenticated: ("AUTH_NOT_AUTHENTICATED", "Not authenticated"),
        PermissionDenied: ("PERMISSION_DENIED", "Not allowed"),
        NotFound: ("RESOURCE_NOT_FOUND", "Resource not found"),
        Throttled: ("RATE_LIMITED", "Too many requests"),
    }
    key = next((k for k in mapping if isinstance(exc, k)), None)
    if key:
        code, title = mapping[key]
        resp.data = {
            "type": f"https://api.conversa.app/problems/{code.lower()}",
            "title": title,
            "status": resp.status_code,
            "detail": title,
            "code": code,
            "params": {},
            "fields": [],
            "trace_id": trace_id,
        }
        return resp

    code = getattr(exc, "default_code", None) or "UNSPECIFIED_ERROR"
    resp.data = {
        "type": f"https://api.conversa.app/problems/{code.lower()}",
        "title": code.replace("_", " ").title(),
        "status": resp.status_code,
        "detail": str(getattr(exc, "detail", "")) or "Error.",
        "code": code,
        "params": {},
        "fields": [],
        "trace_id": trace_id,
    }
    return resp
