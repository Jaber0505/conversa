"""
HTTP request logging middleware.

This middleware logs all HTTP requests with method, path, status code,
and response time for monitoring and debugging.
"""

import time
import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger("http")


class RequestLogMiddleware(MiddlewareMixin):
    """
    Log HTTP request/response details.

    Logs:
    - HTTP method (GET, POST, etc.)
    - Request path
    - Response status code
    - Response time in milliseconds

    Example log output:
        GET /api/v1/events/ -> 200 (45 ms)
    """

    def process_request(self, request):
        """Store request start time."""
        request._start_ts = time.time()

    def process_response(self, request, response):
        """Log request details after response."""
        try:
            start_time = getattr(request, "_start_ts", time.time())
            duration_ms = int((time.time() - start_time) * 1000)

            logger.info(
                "%s %s -> %s (%d ms)",
                request.method,
                request.get_full_path(),
                response.status_code,
                duration_ms,
            )
        except Exception:
            # Silently fail to avoid breaking request processing
            pass

        return response
