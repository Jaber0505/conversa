"""
Custom DRF exception handler for consistent API error responses.

This module provides a centralized exception handler that normalizes all API errors
into a consistent JSON format across the entire application.
"""

from typing import Any, Dict
import logging
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from rest_framework.views import exception_handler as drf_default_handler
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response
from rest_framework import status
try:
    import stripe  # type: ignore
except Exception:  # pragma: no cover - optional at runtime
    stripe = None

try:
    from payments.exceptions import StripeError as PaymentStripeError  # type: ignore
except Exception:  # pragma: no cover - optional at runtime
    class PaymentStripeError(Exception):
        pass

logger = logging.getLogger("django.request")


def _normalize_errors(detail: Any) -> Any:
    """
    Normalize DRF/Django errors into a simple JSON structure.

    Transforms various error formats into a consistent structure:
    - dict/list -> unchanged (DRF ValidationError format)
    - str -> {"non_field_errors": [str]}
    - other -> stringified and wrapped

    Args:
        detail: Error detail from exception

    Returns:
        Normalized error structure
    """
    if isinstance(detail, (dict, list)):
        return detail
    if isinstance(detail, str):
        return {"non_field_errors": [detail]}
    return {"non_field_errors": [str(detail)]}


def drf_exception_handler(exc, context) -> Response:
    """
    Wrap all exceptions in a consistent JSON envelope.

    Response format:
    {
      "status": <HTTP status code>,
      "code": "<error_code_slug>",
      "message": "<human readable message>",
      "errors": {...}  # optional, mainly for 400 validation errors
    }

    Args:
        exc: Exception instance
        context: Request context

    Returns:
        Response: Formatted error response
    """
    # Let DRF build the base response
    response = drf_default_handler(exc, context)

    # Handle common cases not covered by DRF
    if response is None:
        if isinstance(exc, DjangoValidationError):
            data = {
                "status": status.HTTP_400_BAD_REQUEST,
                "code": "validation_error",
                "message": "Invalid data provided.",
                "errors": _normalize_errors(
                    exc.message_dict if hasattr(exc, "message_dict") else exc.messages
                ),
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        if isinstance(exc, IntegrityError):
            data = {
                "status": status.HTTP_409_CONFLICT,
                "code": "conflict",
                "message": "Data conflict (uniqueness or integrity constraint violation).",
            }
            return Response(data, status=status.HTTP_409_CONFLICT)

        # Stripe errors → 502 Bad Gateway (downstream provider)
        if stripe_error_mod = getattr(stripe, 'error', None) if stripe else None\n        stripe_error_cls = getattr(stripe_error_mod, 'StripeError', tuple()) if stripe_error_mod else tuple()\n        if isinstance(exc, stripe_error_cls) or isinstance(exc, PaymentStripeError):\n            data = {
                "status": status.HTTP_502_BAD_GATEWAY,
                "code": "stripe_error",
                "message": str(exc),
            }
            return Response(data, status=status.HTTP_502_BAD_GATEWAY)

        # Generic fallback for unhandled exceptions
        logger.exception("Unhandled server error", exc_info=exc)
        return Response(
            {
                "status": 500,
                "code": "server_error",
                "message": "Internal server error occurred.",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Post-process DRF responses for consistent format
    status_code = response.status_code
    detail = getattr(exc, "detail", None)

    # Map status codes to user-friendly messages
    if status_code == status.HTTP_400_BAD_REQUEST:
        code, message = "validation_error", "Invalid data provided."
        errors = _normalize_errors(
            detail if isinstance(exc, DRFValidationError) else response.data
        )
        payload: Dict[str, Any] = {
            "status": status_code,
            "code": code,
            "message": message,
            "errors": errors,
        }
    elif status_code == status.HTTP_401_UNAUTHORIZED:
        payload = {
            "status": status_code,
            "code": "unauthorized",
            "message": "Authentication required.",
        }
    elif status_code == status.HTTP_403_FORBIDDEN:
        payload = {
            "status": status_code,
            "code": "forbidden",
            "message": "Access denied.",
        }
    elif status_code == status.HTTP_404_NOT_FOUND:
        payload = {
            "status": status_code,
            "code": "not_found",
            "message": "Resource not found.",
        }
    elif status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
        payload = {
            "status": status_code,
            "code": "method_not_allowed",
            "message": "Method not allowed.",
        }
    elif status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE:
        payload = {
            "status": status_code,
            "code": "unsupported_media_type",
            "message": "Unsupported media type.",
        }
    elif status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        payload = {
            "status": status_code,
            "code": "throttled",
            "message": "Too many requests. Please try again later.",
        }
    else:
        # For other status codes, preserve custom exception details if available
        # This handles business exceptions like BookingExpiredError, CancellationDeadlineError, etc.
        exc_code = getattr(exc, "default_code", "error")
        exc_message = str(detail) if detail else "An error occurred."

        payload = {
            "status": status_code,
            "code": exc_code,
            "message": exc_message,
        }

        # If response already has structured data, preserve it
        if isinstance(response.data, dict) and "code" in response.data:
            payload["code"] = response.data.get("code", exc_code)
            payload["message"] = response.data.get("message", exc_message)

    response.data = payload
    return response


