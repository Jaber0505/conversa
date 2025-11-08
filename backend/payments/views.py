"""
Payment API views.

Handles Stripe Checkout session creation and webhook events.
"""
from __future__ import annotations

import re
from urllib.parse import urlencode

from django.conf import settings
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter

from rest_framework import status, views
from rest_framework.response import Response

from common.permissions import IsAuthenticatedAndActive as AuthPerm

from .serializers import (
    CreateCheckoutSessionSerializer,
    CheckoutSessionCreatedSerializer,
    APIErrorSerializer,
    WebhookAckSerializer,
)
from .services import PaymentService
from .validators import validate_stripe_webhook_signature
from .constants import (
    DEFAULT_SUCCESS_PATH,
    DEFAULT_CANCEL_PATH,
    WEBHOOK_EVENT_CHECKOUT_COMPLETED,
    WEBHOOK_EVENT_PAYMENT_FAILED,
    WEBHOOK_EVENT_SESSION_EXPIRED,
)
from bookings.models import Booking


# --- Helper Functions -----------------------------------------------------


def _with_leading_slash(path: str, default: str) -> str:
    """Ensure path starts with /"""
    path = (path or default).strip()
    return path if path.startswith("/") else "/" + path


def _build_return_urls(
    lang: str,
    booking_public_id: str,
    event_id: int,
    success_override: str | None,
    cancel_override: str | None,
):
    """
    Build Stripe success/cancel URLs with proper query parameters.
    """
    if success_override and cancel_override:
        success_url = success_override
        cancel_url = cancel_override
    else:
        success_path = _with_leading_slash(
            getattr(settings, "STRIPE_SUCCESS_PATH", DEFAULT_SUCCESS_PATH),
            DEFAULT_SUCCESS_PATH,
        )
        cancel_path = _with_leading_slash(
            getattr(settings, "STRIPE_CANCEL_PATH", DEFAULT_CANCEL_PATH),
            DEFAULT_CANCEL_PATH,
        )
        base = getattr(settings, "FRONTEND_BASE_URL", "http://localhost:4200").rstrip("/")
        success_url = f"{base}/{lang}{success_path}"
        cancel_url = f"{base}/{lang}{cancel_path}"

    qs = {"b": str(booking_public_id), "e": str(event_id), "lang": lang}
    sep = "&" if "?" in success_url else "?"
    success_url = f"{success_url}{sep}{urlencode(qs)}&cs={{CHECKOUT_SESSION_ID}}"

    sep = "&" if "?" in cancel_url else "?"
    cancel_url = f"{cancel_url}{sep}{urlencode(qs)}"

    return success_url, cancel_url


# --- API Views -------------------------------------------------------------


class CreateCheckoutSessionView(views.APIView):
    """
    Create Stripe Checkout session (TEST mode only).

    Business Rules:
        - User must be authenticated and active
        - Booking must belong to user
        - Booking must be PENDING
        - Maximum 3 payment attempts per booking
        - Zero-amount bookings skip Stripe (direct confirmation)
    """

    permission_classes = [AuthPerm]

    @extend_schema(
        tags=["Payments"],
        operation_id="payments_create_checkout_session",
        summary="Create Stripe Checkout session (TEST only)",
        request=CreateCheckoutSessionSerializer,
        responses={
            201: OpenApiResponse(CheckoutSessionCreatedSerializer, description="Session created"),
            401: OpenApiResponse(APIErrorSerializer, description="Not authenticated"),
            403: OpenApiResponse(APIErrorSerializer, description="User inactive"),
            404: OpenApiResponse(APIErrorSerializer, description="Booking not found"),
            409: OpenApiResponse(
                APIErrorSerializer, description="Booking expired/not payable or retry limit exceeded"
            ),
            502: OpenApiResponse(APIErrorSerializer, description="Stripe API error"),
        },
    )
    def post(self, request):
        """Create checkout session using PaymentService."""
        ser = CreateCheckoutSessionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        booking = get_object_or_404(
            Booking,
            public_id=ser.validated_data["booking_public_id"],
            user=request.user,
        )

        lang = re.sub(r"[^A-Za-z\-]", "", (ser.validated_data.get("lang") or "")).strip() or "fr"

        success_url, cancel_url = _build_return_urls(
            lang=lang,
            booking_public_id=str(booking.public_id),
            event_id=booking.event_id,
            success_override=ser.validated_data.get("success_url"),
            cancel_override=ser.validated_data.get("cancel_url"),
        )

        try:
            stripe_url, session_id, _payment = PaymentService.create_checkout_session(
                booking=booking,
                user=request.user,
                success_url=success_url,
                cancel_url=cancel_url,
            )
            return Response({"url": stripe_url, "session_id": session_id}, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            # Business conflict (booking not payable, expired, retry limit exceeded)
            from rest_framework.exceptions import APIException

            class Conflict(APIException):
                status_code = status.HTTP_409_CONFLICT
                default_code = "conflict"

            raise Conflict(detail=str(e))


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(views.APIView):
    """
    Stripe webhook endpoint (TEST mode).

    Handles Stripe events:
        - checkout.session.completed → Confirms booking and payment
        - payment_intent.payment_failed → Marks payment as failed
        - checkout.session.expired → Marks session as canceled
    """

    authentication_classes = []
    permission_classes = []

    @extend_schema(
        tags=["Payments"],
        operation_id="payments_stripe_webhook",
        summary="Stripe webhook - receives payment events",
        parameters=[
            OpenApiParameter(
                name="Stripe-Signature",
                type=str,
                location=OpenApiParameter.HEADER,
                required=True,
                description="Stripe webhook signature",
            ),
        ],
        request=None,
        responses={
            200: OpenApiResponse(WebhookAckSerializer, description='Event acknowledged ({"detail":"ok"})'),
            400: OpenApiResponse(APIErrorSerializer, description="Invalid signature/payload"),
            500: OpenApiResponse(APIErrorSerializer, description="Webhook secret missing"),
        },
    )
    def post(self, request):
        """Handle Stripe webhook events."""
        import logging

        logger = logging.getLogger("payments.webhook")
        logger.info("Webhook received from Stripe")

        webhook_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", "")
        if not webhook_secret:
            logger.error("Webhook secret missing in settings")
            from rest_framework.exceptions import APIException

            class ServerError(APIException):
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                default_code = "server_error"

            raise ServerError(detail="Webhook secret missing")

        # Require presence of Stripe-Signature header (tests expect 400 if missing)
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
        if not sig_header:
            from rest_framework.exceptions import ValidationError as DRFValidationError
            raise DRFValidationError(detail="Missing Stripe-Signature header")
        try:
            event = validate_stripe_webhook_signature(
                payload=request.body, sig_header=sig_header, webhook_secret=webhook_secret
            )
        except ValidationError as e:
            logger.error(f"Webhook signature validation failed: {str(e)}")
            from rest_framework.exceptions import ValidationError as DRFValidationError

            raise DRFValidationError(detail=str(e))

        event_type = event.get("type")
        data = event.get("data", {}).get("object", {})
        logger.info(f"Event type: {event_type}")

        if event_type == WEBHOOK_EVENT_CHECKOUT_COMPLETED:
            booking_public_id = (
                (data.get("metadata") or {}).get("booking_public_id") or data.get("client_reference_id")
            )
            session_id = data.get("id")
            payment_intent_id = data.get("payment_intent")

            if booking_public_id:
                PaymentService.confirm_payment_from_webhook(
                    booking_public_id=booking_public_id,
                    session_id=session_id,
                    payment_intent_id=payment_intent_id,
                    raw_event=data,
                )
            else:
                logger.warning("No booking_public_id found in webhook data")

        elif event_type == WEBHOOK_EVENT_PAYMENT_FAILED:
            payment_intent_id = data.get("id")
            session_id = (data.get("metadata") or {}).get("stripe_session_id")
            reason = (data.get("last_payment_error") or {}).get("message")
            PaymentService.mark_payment_failed(
                session_id=session_id,
                payment_intent_id=payment_intent_id,
                reason=reason,
                raw_event=data,
            )

        elif event_type == WEBHOOK_EVENT_SESSION_EXPIRED:
            session_id = data.get("id")
            if session_id:
                PaymentService.mark_session_canceled(session_id)

        else:
            logger.info(f"Unhandled event type: {event_type}")

        return Response({"detail": "ok"}, status=status.HTTP_200_OK)
