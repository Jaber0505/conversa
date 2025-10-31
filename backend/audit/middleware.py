"""
Audit middleware for logging HTTP API requests.

Logs all API requests with user, method, path, status code, IP, and duration.
Skips health checks and static assets to reduce noise.
Automatically categorizes requests and assigns appropriate log levels.
"""
import time
from django.utils.deprecation import MiddlewareMixin
from .models import AuditLog


# Paths to skip from audit logs (health checks, docs, static files)
SKIP_PATH_PREFIXES = (
    "/healthz",
    "/api/schema",
    "/api/docs",
    "/api/redoc",
    "/static",
    "/admin/jsi18n",
    "/favicon",
)


def _client_ip(request):
    """
    Extract client IP from request, considering X-Forwarded-For header.

    Args:
        request: Django request object

    Returns:
        str: Client IP address
    """
    xfwd = request.META.get("HTTP_X_FORWARDED_FOR")
    if xfwd:
        return xfwd.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _determine_category(path):
    """
    Determine audit log category based on request path.

    Args:
        path: Request path (e.g., /api/v1/auth/login/)

    Returns:
        str: AuditLog category
    """
    # Check in priority order (most specific first)
    if "/admin/" in path:
        return AuditLog.Category.ADMIN
    elif "/auth/" in path or "/token/" in path:
        return AuditLog.Category.AUTH
    elif "/events/" in path:
        return AuditLog.Category.EVENT
    elif "/bookings/" in path:
        return AuditLog.Category.BOOKING
    elif "/payments/" in path:
        return AuditLog.Category.PAYMENT
    elif "/partners/" in path:
        return AuditLog.Category.PARTNER
    elif "/users/" in path or "/profile/" in path:
        return AuditLog.Category.USER
    else:
        return AuditLog.Category.HTTP


def _determine_level(status_code):
    """
    Determine log level based on HTTP status code.

    Args:
        status_code: HTTP response status code

    Returns:
        str: AuditLog level
    """
    if status_code >= 500:
        return AuditLog.Level.ERROR
    elif status_code >= 400:
        return AuditLog.Level.WARNING
    elif status_code >= 300:
        return AuditLog.Level.DEBUG
    else:
        return AuditLog.Level.INFO


class AuditMiddleware(MiddlewareMixin):
    """
    Middleware to log all HTTP API requests to AuditLog model.

    Automatically categorizes requests and assigns log levels based on
    the request path and response status code.
    """

    def process_request(self, request):
        """Record request start time."""
        request._audit_start = time.perf_counter()

    def process_response(self, request, response):
        """Log request details after response is ready."""
        try:
            path = request.path or ""

            # Skip paths that shouldn't be audited
            if path.startswith(SKIP_PATH_PREFIXES):
                return response

            # Calculate request duration in milliseconds
            duration_ms = int(
                (time.perf_counter() - getattr(request, "_audit_start", time.perf_counter()))
                * 1000
            )

            status_code = getattr(response, "status_code", 0)

            # Create audit log entry with categorization
            AuditLog.objects.create(
                category=_determine_category(path),
                level=_determine_level(status_code),
                action=f"{request.method} {path}",
                message=f"{request.method} {path} → {status_code} ({duration_ms}ms)",
                user=(
                    request.user
                    if hasattr(request, "user") and request.user.is_authenticated
                    else None
                ),
                method=request.method,
                path=path[:255],
                status_code=status_code,
                ip=_client_ip(request),
                user_agent=(request.META.get("HTTP_USER_AGENT") or "")[:255],
                duration_ms=max(duration_ms, 0),
            )
        except Exception:
            # Never block response if audit logging fails
            pass

        return response
