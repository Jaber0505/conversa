"""
Payment API views.

Handles Stripe Checkout session creation and webhook events.
"""
import re
from urllib.parse import urlencode

from django.conf import settings
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from drf_spectacular.utils import (
    extend_schema, OpenApiResponse, OpenApiExample, OpenApiParameter
)

from rest_framework import status, views
from rest_framework.response import Response

from common.permissions import IsAuthenticatedAndActive as AuthPerm

from .serializers import (
    CreateCheckoutSessionSerializer,
    CheckoutSessionCreatedSerializer,
    APIErrorSerializer,
    WebhookAckSerializer,
)
from .services import PaymentService, RefundService
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


def _build_return_urls(lang: str, booking_public_id: str, success_override: str | None, cancel_override: str | None):
    """
    Build Stripe success/cancel URLs.

    Args:
        lang: Language code (e.g., "fr", "en")
        booking_public_id: Booking UUID
        success_override: Custom success URL (optional - must provide both or neither)
        cancel_override: Custom cancel URL (optional - must provide both or neither)

    Returns:
        tuple: (success_url, cancel_url)

    Note:
        Both success_override and cancel_override must be provided together.
        If only one is provided, both will be ignored and defaults will be used.
    """
    # Use overrides only if BOTH are provided (prevents partial override bugs)
    if success_override and cancel_override:
        success_url = success_override
        cancel_url = cancel_override
    else:
        success_path = _with_leading_slash(
            getattr(settings, "STRIPE_SUCCESS_PATH", DEFAULT_SUCCESS_PATH),
            DEFAULT_SUCCESS_PATH
        )
        cancel_path = _with_leading_slash(
            getattr(settings, "STRIPE_CANCEL_PATH", DEFAULT_CANCEL_PATH),
            DEFAULT_CANCEL_PATH
        )
        base = getattr(settings, "FRONTEND_BASE_URL", "http://localhost:4200").rstrip("/")
        success_url = f"{base}/{lang}{success_path}"
        cancel_url = f"{base}/{lang}{cancel_path}"

    # Add query params (check if URL already has params)
    qs = {"b": str(booking_public_id), "lang": lang}
    separator = "&" if "?" in success_url else "?"
    success_url = f"{success_url}{separator}{urlencode(qs)}&cs={{CHECKOUT_SESSION_ID}}"

    separator = "&" if "?" in cancel_url else "?"
    cancel_url = f"{cancel_url}{separator}{urlencode(qs)}"

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
        description=(
            "Creates a Stripe Checkout session for a pending booking.\n\n"
            "**Business Rules:**\n"
            "- TEST mode only (sk_test_ keys)\n"
            "- Booking must be PENDING and not expired\n"
            "- Maximum 3 payment attempts per booking\n"
            "- Zero-amount bookings are confirmed directly\n\n"
            "**Returns:**\n"
            "Stripe Checkout URL where user should be redirected to complete payment."
        ),
        request=CreateCheckoutSessionSerializer,
        responses={
            201: OpenApiResponse(CheckoutSessionCreatedSerializer, description="Session created"),
            401: OpenApiResponse(APIErrorSerializer, description="Not authenticated"),
            403: OpenApiResponse(APIErrorSerializer, description="User inactive"),
            404: OpenApiResponse(APIErrorSerializer, description="Booking not found"),
            409: OpenApiResponse(APIErrorSerializer, description="Booking expired/not payable or retry limit exceeded"),
            502: OpenApiResponse(APIErrorSerializer, description="Stripe API error"),
        },
        examples=[
            OpenApiExample(
                "Request",
                value={"booking_public_id": "11111111-1111-1111-1111-111111111111", "lang": "fr"},
                request_only=True,
            ),
            OpenApiExample(
                "Response - Success",
                value={"url": "https://checkout.stripe.com/c/pay/cs_test_abc123", "session_id": "cs_test_abc123"},
                response_only=True,
            ),
            OpenApiExample(
                "Error - Booking expired",
                value={"detail": "Booking has expired and was cancelled."},
                response_only=True,
                status_codes=["409"],
            ),
            OpenApiExample(
                "Error - Retry limit",
                value={"detail": "Payment retry limit exceeded (3 attempts). Please contact support."},
                response_only=True,
                status_codes=["409"],
            ),
        ],
    )
    def post(self, request):
        """Create checkout session using PaymentService."""
        # Validate serializer
        ser = CreateCheckoutSessionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        # Get booking (must belong to user)
        booking = get_object_or_404(
            Booking,
            public_id=ser.validated_data["booking_public_id"],
            user=request.user
        )

        # Clean language code
        lang = re.sub(r"[^A-Za-z\-]", "", (ser.validated_data.get("lang") or "")).strip() or "fr"

        # Build return URLs
        success_url, cancel_url = _build_return_urls(
            lang=lang,
            booking_public_id=str(booking.public_id),
            success_override=ser.validated_data.get("success_url"),
            cancel_override=ser.validated_data.get("cancel_url"),
        )

        try:
            # Use service to create checkout session
            stripe_url, session_id, payment = PaymentService.create_checkout_session(
                booking=booking,
                user=request.user,
                success_url=success_url,
                cancel_url=cancel_url,
            )

            # DEVELOPMENT SIMULATOR: Auto-confirm payment if enabled
            # This simulates what the Stripe webhook would do in production
            if getattr(settings, 'STRIPE_CONFIRM_SIMULATOR_ENABLED', False) and session_id:
                # Simulate successful payment immediately
                PaymentService.confirm_payment_from_webhook(
                    booking_public_id=str(booking.public_id),
                    session_id=session_id,
                    payment_intent_id=f"pi_test_simulated_{session_id}",
                    raw_event={"type": "checkout.session.completed", "simulated": True}
                )

            return Response(
                {"url": stripe_url, "session_id": session_id},
                status=status.HTTP_201_CREATED
            )

        except ValidationError as e:
            # Business rule validation failed
            return Response(
                {"detail": str(e)},
                status=status.HTTP_409_CONFLICT
            )
        except Exception as e:
            # Stripe or other errors
            return Response(
                {"detail": str(e)},
                status=status.HTTP_502_BAD_GATEWAY
            )


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(views.APIView):
    """
    Stripe webhook endpoint (TEST mode).

    Handles Stripe events:
        - checkout.session.completed → Confirms booking and payment
        - payment_intent.payment_failed → Marks payment as failed
        - checkout.session.expired → Marks session as canceled

    Security:
        - Public endpoint (no authentication)
        - Signature verification required (Stripe-Signature header)
    """
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        tags=["Payments"],
        operation_id="payments_stripe_webhook",
        summary="Stripe webhook - receives payment events",
        description=(
            "Public endpoint called by Stripe. Verifies `Stripe-Signature` header.\n\n"
            "**Events Handled:**\n"
            "- `checkout.session.completed` → Confirms booking + payment\n"
            "- `payment_intent.payment_failed` → Marks payment as failed\n"
            "- `checkout.session.expired` → Marks session as canceled\n\n"
            "**Security:**\n"
            "Webhook signature must be valid (configured in settings.STRIPE_WEBHOOK_SECRET)."
        ),
        parameters=[
            OpenApiParameter(
                name="Stripe-Signature",
                type=str,
                location=OpenApiParameter.HEADER,
                required=True,
                description="Stripe webhook signature"
            ),
        ],
        request=None,
        responses={
            200: OpenApiResponse(WebhookAckSerializer, description='Event acknowledged ({"detail":"ok"})'),
            400: OpenApiResponse(APIErrorSerializer, description="Invalid signature/payload"),
            500: OpenApiResponse(APIErrorSerializer, description="Webhook secret missing"),
        },
        examples=[
            OpenApiExample(
                "Event - checkout.session.completed",
                value={
                    "type": "checkout.session.completed",
                    "data": {
                        "object": {
                            "id": "cs_test_abc123",
                            "payment_intent": "pi_3XYZ...",
                            "client_reference_id": "11111111-1111-1111-1111-111111111111",
                            "metadata": {"booking_public_id": "11111111-1111-1111-1111-111111111111"}
                        }
                    }
                },
                request_only=True,
            ),
            OpenApiExample(
                "Response",
                value={"detail": "ok"},
                response_only=True,
            ),
        ],
    )
    def post(self, request):
        """Handle Stripe webhook events."""
        # Check webhook secret
        webhook_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", "")
        if not webhook_secret:
            return Response(
                {"detail": "Webhook secret missing"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Verify signature
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
        try:
            event = validate_stripe_webhook_signature(
                payload=request.body,
                sig_header=sig_header,
                webhook_secret=webhook_secret
            )
        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Extract event data
        event_type = event.get("type")
        data = event.get("data", {}).get("object", {})

        # Handle checkout.session.completed
        if event_type == WEBHOOK_EVENT_CHECKOUT_COMPLETED:
            booking_public_id = (
                (data.get("metadata") or {}).get("booking_public_id") or
                data.get("client_reference_id")
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

        # Handle payment_intent.payment_failed
        elif event_type == WEBHOOK_EVENT_PAYMENT_FAILED:
            payment_intent_id = data.get("id")
            if payment_intent_id:
                PaymentService.mark_payment_failed(payment_intent_id)

        # Handle checkout.session.expired
        elif event_type == WEBHOOK_EVENT_SESSION_EXPIRED:
            session_id = data.get("id")
            if session_id:
                PaymentService.mark_session_canceled(session_id)

        return Response({"detail": "ok"}, status=status.HTTP_200_OK)
