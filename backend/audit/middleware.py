# backend/audit/middleware.py
import time
from django.utils.deprecation import MiddlewareMixin
from .models import AuditLog

SKIP_PATH_PREFIXES = ("/healthz", "/api/schema", "/api/docs", "/api/redoc", "/static", "/admin/js", "/favicon")

def _client_ip(request):
    xfwd = request.META.get("HTTP_X_FORWARDED_FOR")
    if xfwd:
        return xfwd.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")

class AuditMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request._t0 = time.perf_counter()

    def process_response(self, request, response):
        try:
            path = request.path or ""
            if path.startswith(SKIP_PATH_PREFIXES):
                return response
            dur = int(((time.perf_counter() - getattr(request, "_t0", time.perf_counter())) * 1000))
            AuditLog.objects.create(
                user=getattr(request, "user", None) if getattr(request, "user", None) and request.user.is_authenticated else None,
                method=request.method,
                path=path[:255],
                status_code=getattr(response, "status_code", 0),
                ip=_client_ip(request),
                user_agent=(request.META.get("HTTP_USER_AGENT") or "")[:255],
                duration_ms=max(dur, 0),
            )
        except Exception:
            # ne bloque jamais la réponse si l’audit échoue
            pass
        return response
