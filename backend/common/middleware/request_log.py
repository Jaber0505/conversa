# backend/common/middleware/request_log.py
import time
import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger("http")

class RequestLogMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request._start_ts = time.time()

    def process_response(self, request, response):
        try:
            dur_ms = int((time.time() - getattr(request, "_start_ts", time.time())) * 1000)
            logger.info("%s %s -> %s (%d ms)",
                        request.method, request.get_full_path(), response.status_code, dur_ms)
        except Exception:
            pass
        return response
