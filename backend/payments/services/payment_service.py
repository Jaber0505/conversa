"""
Payment service for Stripe integration.

Handles payment session creation, confirmation, and status updates.
"""
import stripe
from django.conf import settings
from django.db import transaction

from common.services.base import BaseService
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
    def _initialize_stripe():
        """Initialize Stripe with TEST key."""
        validate_stripe_test_mode()
        stripe.api_key = settings.STRIPE_SECRET_KEY

    @staticmethod
    def create_checkout_session(booking, user, success_url, cancel_url):
        """
        Create a Stripe Checkout session for a booking.

        Business Rules:
            - Booking must be PENDING
            - Booking must not be expired
            - Maximum retry limit not exceeded
            - If amount = 0 → bypass Stripe, confirm directly

        Args:
            booking: Booking instance
            user: User making payment
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect after cancelled payment

        Returns:
            tuple: (stripe_session_url, session_id, payment_instance)
                   For zero amount: (success_url, None, payment_instance)

        Raises:
            ValidationError: If booking not payable or retry limit exceeded
            stripe.error.StripeError: If Stripe API fails
        """
        # Validate business rules
        validate_booking_is_payable(booking)
        validate_payment_retry_limit(booking)

        # Get currency (ensure it's a valid 3-character ISO code)
        currency_raw = (
            getattr(booking, "currency", None) or
            getattr(settings, "STRIPE_CURRENCY", None) or
            DEFAULT_PAYMENT_CURRENCY
        )
        # Ensure currency is valid 3-letter code
        currency = str(currency_raw).upper().strip()[:3] if currency_raw else "EUR"

        # Handle zero amount (free booking)
        if booking.amount_cents <= 0:
            return PaymentService._handle_zero_amount_payment(
                booking, user, currency, success_url
            )

        # Create Stripe Checkout session
        PaymentService._initialize_stripe()

        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[{
                "price_data": {
                    "currency": currency.lower(),
                    "unit_amount": int(booking.amount_cents),
                    "product_data": {
                        "name": getattr(booking.event, "title", "Conversa - Language Exchange Event")
                    },
                },
                "quantity": BOOKING_QUANTITY,  # Always 1 seat per booking
            }],
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

        # Create NEW Payment record (each retry = new Stripe session = new Payment)
        # This ensures validate_payment_retry_limit() correctly counts attempts
        # and provides complete audit trail of all payment attempts
        payment = Payment.objects.create(
            booking=booking,
            user=user,
            stripe_checkout_session_id=session.id,
            amount_cents=int(booking.amount_cents),
            currency=currency,
            status=STATUS_PENDING,
        )

        # Log payment creation
        from audit.services import AuditService
        AuditService.log_payment_created(payment, user)

        return session.url, session.id, payment

    @staticmethod
    @transaction.atomic
    def _handle_zero_amount_payment(booking, user, currency, success_url):
        """
        Handle zero-amount payments (free bookings).

        Directly confirms booking without Stripe.

        Args:
            booking: Booking instance
            user: User
            currency: Currency code
            success_url: Success redirect URL

        Returns:
            tuple: (success_url, None, payment_instance)
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
        from audit.services import AuditService
        AuditService.log_payment_succeeded(payment, user, is_free=True)

        return success_url, None, payment

    @staticmethod
    @transaction.atomic
    def confirm_payment_from_webhook(booking_public_id, session_id, payment_intent_id, raw_event):
        """
        Confirm payment after successful Stripe checkout.

        Called from webhook handler when checkout.session.completed is received.

        Args:
            booking_public_id: Booking UUID
            session_id: Stripe session ID
            payment_intent_id: Stripe payment intent ID
            raw_event: Raw Stripe event data (for audit)

        Returns:
            Payment: Updated payment instance or None if booking not found
        """
        from bookings.models import Booking

        try:
            booking = Booking.objects.select_for_update().get(public_id=booking_public_id)
        except Booking.DoesNotExist:
            return None

        # Confirm booking if still pending
        if booking.status == BookingStatus.PENDING:
            booking.mark_confirmed(payment_intent_id=payment_intent_id)

        # Get or create payment
        currency_raw = booking.currency or DEFAULT_PAYMENT_CURRENCY
        currency = str(currency_raw).upper().strip()[:3] if currency_raw else "EUR"

        payment, created = Payment.objects.get_or_create(
            booking=booking,
            user=booking.user,
            defaults={
                "amount_cents": int(booking.amount_cents),
                "currency": currency,
                "status": STATUS_PENDING,
            },
        )

        # Update payment
        if session_id:
            payment.stripe_checkout_session_id = payment.stripe_checkout_session_id or session_id
        if payment_intent_id:
            payment.stripe_payment_intent_id = payment.stripe_payment_intent_id or payment_intent_id

        payment.status = STATUS_SUCCEEDED
        payment.raw_event = raw_event
        payment.save()

        # Log success
        from audit.services import AuditService
        AuditService.log_payment_succeeded(payment, booking.user)

        return payment

    @staticmethod
    def mark_payment_failed(payment_intent_id):
        """
        Mark payment as failed.

        Called from webhook when payment_intent.payment_failed is received.

        Args:
            payment_intent_id: Stripe PaymentIntent ID

        Returns:
            int: Number of payments updated
        """
        count = Payment.objects.filter(
            stripe_payment_intent_id=payment_intent_id
        ).update(status=STATUS_FAILED)

        # Log failures
        if count > 0:
            from audit.services import AuditService
            payments = Payment.objects.filter(stripe_payment_intent_id=payment_intent_id)
            for payment in payments:
                AuditService.log_payment_failed(payment, payment.user)

        return count

    @staticmethod
    def mark_session_canceled(session_id):
        """
        Mark payment session as canceled/expired.

        Called from webhook when checkout.session.expired is received.

        Args:
            session_id: Stripe Checkout Session ID

        Returns:
            int: Number of payments updated
        """
        count = Payment.objects.filter(
            stripe_checkout_session_id=session_id,
            status=STATUS_PENDING
        ).update(status=STATUS_CANCELED)

        return count

    @staticmethod
    def get_payment_by_booking(booking):
        """
        Get the latest successful payment for a booking.

        Args:
            booking: Booking instance

        Returns:
            Payment or None: Latest succeeded payment
        """
        return Payment.objects.filter(
            booking=booking,
            status=STATUS_SUCCEEDED
        ).order_by('-created_at').first()
