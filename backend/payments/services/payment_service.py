"""
Payment service for Stripe integration.

Handles payment session creation, confirmation, and status updates.
"""
from __future__ import annotations

import stripe
from django.conf import settings
from django.db import transaction
from django.core.exceptions import ValidationError

from common.services.base import BaseService
from audit.services import AuditService
from ..models import Payment
from ..constants import (
    DEFAULT_PAYMENT_CURRENCY,
    BOOKING_QUANTITY,
    STATUS_PENDING,
    STATUS_SUCCEEDED,
    STATUS_FAILED,
    STATUS_CANCELED,
)
from ..validators import (
    validate_stripe_test_mode,
    validate_booking_is_payable,
    validate_payment_retry_limit,
)
from bookings.models import BookingStatus


class PaymentService(BaseService):
    """Service for payment operations."""

    @staticmethod
    def _initialize_stripe() -> None:
        """Initialize Stripe with TEST key."""
        validate_stripe_test_mode()
        stripe.api_key = settings.STRIPE_SECRET_KEY

    @staticmethod
    def _get_valid_pending_payment(booking):
        """
        Get the most recent PENDING payment for a booking.

        Returns:
            Payment or None: Latest PENDING payment with a valid session ID
        """
        return (
            Payment.objects.filter(
                booking=booking,
                status=STATUS_PENDING,
                stripe_checkout_session_id__isnull=False
            )
            .order_by("-created_at")
            .first()
        )

    @staticmethod
    def create_checkout_session(booking, user, success_url: str, cancel_url: str):
        """
        Create a Stripe Checkout session for a booking.

        Business Rules:
            - Booking must be PENDING
            - Booking must not be expired
            - Maximum retry limit not exceeded
            - If amount = 0 → bypass Stripe, confirm directly
            - Reuses existing PENDING payment session if still valid (not expired)

        Args:
            booking: Booking instance
            user: User making payment
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect after cancelled payment

        Returns:
            tuple: (stripe_session_url, session_id, payment_instance)
                   For zero amount: (None, None, payment_instance)

        Raises:
            ValidationError: If booking not payable or retry limit exceeded
            stripe.error.StripeError: If Stripe API fails
        """
        # Validate business rules
        validate_booking_is_payable(booking)
        validate_payment_retry_limit(booking)

        # Get currency (ensure it's a valid 3-character ISO code)
        currency_raw = (
            getattr(booking, "currency", None)
            or getattr(settings, "STRIPE_CURRENCY", None)
            or DEFAULT_PAYMENT_CURRENCY
        )
        currency = str(currency_raw).upper().strip()[:3] if currency_raw else "EUR"

        # Handle zero amount (free booking)
        if booking.amount_cents <= 0:
            return PaymentService._handle_zero_amount_payment(
                booking, user, currency, success_url
            )

        # Check if there's an existing PENDING payment for this booking
        existing_payment = PaymentService._get_valid_pending_payment(booking)
        if existing_payment:
            # Reuse existing session ONLY if booking is still valid (not expired)
            # This prevents reusing a session for an expired booking
            if not booking.is_expired:
                PaymentService._initialize_stripe()
                try:
                    session = stripe.checkout.Session.retrieve(existing_payment.stripe_checkout_session_id)
                    # Only reuse if session is still open (not expired)
                    if session.status == 'open':
                        return session.url, session.id, existing_payment
                    else:
                        # Session expired, mark as canceled and create new one
                        existing_payment.status = STATUS_CANCELED
                        existing_payment.save(update_fields=['status', 'updated_at'])
                except stripe.error.StripeError:
                    # Session not found or error, mark as canceled and create new one
                    existing_payment.status = STATUS_CANCELED
                    existing_payment.save(update_fields=['status', 'updated_at'])
            else:
                # Booking is expired, mark payment as canceled
                existing_payment.status = STATUS_CANCELED
                existing_payment.save(update_fields=['status', 'updated_at'])

        # Create Stripe Checkout session
        PaymentService._initialize_stripe()

        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[
                {
                    "price_data": {
                        "currency": currency.lower(),
                        "unit_amount": int(booking.amount_cents),
                        "product_data": {
                            "name": getattr(
                                booking.event, "title", "Conversa - Language Exchange Event"
                            )
                        },
                    },
                    "quantity": BOOKING_QUANTITY,  # Always 1 seat per booking
                }
            ],
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=user.email,
            client_reference_id=str(booking.public_id),
            metadata={
                "booking_public_id": str(booking.public_id),
                "user_id": str(user.id),
            },
            payment_intent_data={
                "metadata": {
                    "booking_public_id": str(booking.public_id),
                    "user_id": str(user.id),
                }
            },
        )

        # Create new Payment record (each retry = new Stripe session)
        payment = Payment.objects.create(
            booking=booking,
            user=user,
            stripe_checkout_session_id=session.id,
            amount_cents=int(booking.amount_cents),
            currency=currency,
            status=STATUS_PENDING,
        )

        # Log payment creation
        AuditService.log_payment_created(payment, user)

        return session.url, session.id, payment

    @staticmethod
    @transaction.atomic
    def _handle_zero_amount_payment(booking, user, currency: str, success_url: str):
        """
        Handle zero-amount payments (free bookings).

        Directly confirms booking without Stripe.

        Returns:
            tuple: (None, None, payment_instance)
        """
        # Confirm booking using service (will also publish event if organizer)
        from bookings.services import BookingService

        BookingService.confirm_booking(booking=booking, payment_intent_id=None)

        # Create succeeded payment record
        payment = Payment.objects.create(
            user=user,
            booking=booking,
            amount_cents=0,
            currency=currency,
            status=STATUS_SUCCEEDED,
        )

        # Log payment
        AuditService.log_payment_succeeded(payment, user, is_free=True)

        return None, None, payment

    @staticmethod
    @transaction.atomic
    def confirm_payment_from_webhook(
        booking_public_id: str, session_id: str | None, payment_intent_id: str | None, raw_event
    ):
        """
        Confirm payment after successful Stripe checkout.

        Called from webhook handler when checkout.session.completed is received.

        Returns:
            Payment: Updated payment instance
        """
        import logging

        logger = logging.getLogger("payments.webhook")

        from bookings.models import Booking

        logger.info(f"Looking for booking {booking_public_id}")

        try:
            booking = Booking.objects.select_for_update().get(public_id=booking_public_id)
            logger.info(
                f"Booking found: ID={booking.id}, Status={booking.status}, Event={booking.event_id}"
            )
        except Booking.DoesNotExist:
            logger.error(f"Booking {booking_public_id} not found")
            raise ValidationError("Booking not found")

        # Confirm booking if still pending (use service to trigger side-effects like event publish)
        if booking.status == BookingStatus.PENDING:
            logger.info("Booking is PENDING, confirming via BookingService")
            from bookings.services import BookingService
            BookingService.confirm_booking(booking=booking, payment_intent_id=payment_intent_id)
            logger.info("Booking marked as CONFIRMED (service)")
        else:
            logger.info(f"Booking status is {booking.status}, skipping confirmation")

        # Find existing payment by session id for this booking
        try:
            payment = Payment.objects.get(
                booking=booking,
                stripe_checkout_session_id=session_id,
            )
        except Payment.DoesNotExist:
            logger.error(
                f"Payment not found for booking {booking.id} and session {session_id}"
            )
            raise ValidationError("Payment not found")

        # Update payment
        if payment_intent_id:
            payment.stripe_payment_intent_id = payment_intent_id
        payment.status = STATUS_SUCCEEDED
        payment.raw_event = raw_event
        payment.save()

        logger.info(f"Payment #{payment.id} marked as SUCCEEDED")

        # Log success
        AuditService.log_payment_succeeded(payment, booking.user, is_free=False)

        logger.info(f"Payment confirmation complete for booking {booking_public_id}")

        return payment

    @staticmethod
    def mark_payment_failed(
        session_id: str | None = None,
        payment_intent_id: str | None = None,
        reason: str | None = None,
        raw_event: dict | None = None,
    ) -> int:
        """
        Mark payment as failed.

        Called from webhook when payment_intent.payment_failed is received.

        Args:
            session_id: Stripe Checkout Session ID (preferred)
            payment_intent_id: Stripe PaymentIntent ID (fallback)
            reason: Optional failure reason message
            raw_event: Optional raw Stripe object for audit

        Returns:
            int: Number of payments updated
        """
        qs = Payment.objects.all()
        if session_id:
            qs = qs.filter(stripe_checkout_session_id=session_id)
        elif payment_intent_id:
            qs = qs.filter(stripe_payment_intent_id=payment_intent_id)
        else:
            return 0

        count = qs.update(status=STATUS_FAILED)

        if count > 0:
            for payment in qs:
                if raw_event is not None:
                    payment.raw_event = raw_event
                    payment.save(update_fields=["raw_event", "status"])  # status already updated
                AuditService.log_payment_failed(
                    payment, payment.user, error_message=reason or "payment_failed"
                )

        return count

    @staticmethod
    def mark_session_canceled(session_id: str) -> int:
        """
        Mark payment session as canceled/expired.

        Called from webhook when checkout.session.expired is received.

        Args:
            session_id: Stripe Checkout Session ID

        Returns:
            int: Number of payments updated
        """
        count = (
            Payment.objects.filter(
                stripe_checkout_session_id=session_id, status=STATUS_PENDING
            ).update(status=STATUS_CANCELED)
        )

        return count

    @staticmethod
    def get_payment_by_booking(booking):
        """
        Get the latest successful payment for a booking.

        Returns:
            Payment or None: Latest succeeded payment
        """
        return (
            Payment.objects.filter(booking=booking, status=STATUS_SUCCEEDED)
            .order_by("-created_at")
            .first()
        )
