"""
Refund service for Stripe integration.

Handles automatic refunds when bookings are cancelled.
"""
import stripe
from django.conf import settings
from django.db import transaction

from common.services.base import BaseService
from ..models import Payment
from ..constants import STATUS_SUCCEEDED
from ..validators import validate_stripe_test_mode, validate_refund_eligibility
from ..exceptions import (
    RefundProcessingError,
    PaymentIntentMissingError,
    StripeError as PaymentStripeError,
)


class RefundService(BaseService):
    """Service for refund operations."""

    @staticmethod
    def _initialize_stripe():
        """Initialize Stripe with TEST key."""
        validate_stripe_test_mode()
        stripe.api_key = settings.STRIPE_SECRET_KEY

    @staticmethod
    @transaction.atomic
    def process_refund(booking, cancelled_by):
        """
        Process automatic refund for a cancelled booking.

        Business Rules:
            - Booking must be CONFIRMED
            - Must be at least 3h before event
            - Only refunds if payment was successful

        Args:
            booking: Booking instance to refund
            cancelled_by: User who cancelled (for audit)

        Returns:
            tuple: (refund_success: bool, message: str, payment: Payment or None)

        Raises:
            ValidationError: If refund not allowed
        """
        # Validate eligibility
        validate_refund_eligibility(booking)

        # Find the successful payment
        payment = Payment.objects.filter(
            booking=booking,
            status=STATUS_SUCCEEDED
        ).order_by('-created_at').first()

        if not payment:
            return False, "No successful payment found for this booking", None

        # If zero amount (free booking), just mark as refunded
        if booking.amount_cents == 0:
            return RefundService._handle_zero_amount_refund(booking, payment, cancelled_by)

        # Check if already refunded (for paid bookings only)
        if payment.amount_cents <= 0:
            return False, "Payment already refunded", payment

        # Process Stripe refund
        return RefundService._process_stripe_refund(booking, payment, cancelled_by)

    @staticmethod
    def _handle_zero_amount_refund(booking, payment, cancelled_by):
        """
        Handle refund for zero-amount (free) bookings.

        Args:
            booking: Booking instance
            payment: Payment instance
            cancelled_by: User who cancelled

        Returns:
            tuple: (True, message, payment)
        """
        # Ensure currency is valid 3-letter code
        currency = str(payment.currency).upper().strip()[:3] if payment.currency else "EUR"

        # Create negative payment record for audit trail
        refund_payment = Payment.objects.create(
            user=payment.user,
            booking=booking,
            amount_cents=0,
            currency=currency,
            status=STATUS_SUCCEEDED,
            raw_event={"type": "free_booking_cancellation", "refund": True},
        )

        # Log refund
        from audit.services import AuditService
        AuditService.log_payment_refunded(
            refund_payment,
            cancelled_by,
            reason="Free booking cancelled",
            is_free=True
        )

        return True, "Free booking cancelled (no refund needed)", refund_payment

    @staticmethod
    def _process_stripe_refund(booking, payment, cancelled_by):
        """
        Process actual Stripe refund.

        Args:
            booking: Booking instance
            payment: Payment instance
            cancelled_by: User who cancelled

        Returns:
            tuple: (success, message, refund_payment or None)
        """
        RefundService._initialize_stripe()

        # Get payment intent ID
        payment_intent_id = payment.stripe_payment_intent_id

        if not payment_intent_id:
            raise PaymentIntentMissingError(
                f"Payment {payment.id} has no payment_intent_id - cannot refund"
            )

        try:
            # Create Stripe refund
            refund = stripe.Refund.create(
                payment_intent=payment_intent_id,
                metadata={
                    "booking_public_id": str(booking.public_id),
                    "cancelled_by_user_id": str(cancelled_by.id),
                    "reason": "booking_cancelled",
                },
            )

            # Ensure currency is valid 3-letter code
            currency = str(payment.currency).upper().strip()[:3] if payment.currency else "EUR"

            # Create refund payment record (negative amount)
            refund_payment = Payment.objects.create(
                user=payment.user,
                booking=booking,
                amount_cents=-abs(payment.amount_cents),  # Negative for refund
                currency=currency,
                status=STATUS_SUCCEEDED,
                stripe_payment_intent_id=payment_intent_id,
                raw_event={
                    "type": "refund",
                    "refund_id": str(refund.id),
                    "amount": int(getattr(refund, "amount", 0)) if hasattr(refund, "amount") else 0,
                    "status": str(getattr(refund, "status", "")),
                },
            )

            # Log refund
            from audit.services import AuditService

            AuditService.log_payment_refunded(
                refund_payment,
                cancelled_by,
                amount_cents=payment.amount_cents,
                refund_id=refund.id,
            )

            return True, f"Refund processed: {refund.id}", refund_payment

        except (ValueError, TypeError) as e:
            # Handle data serialization errors (JSON, type conversion, etc.)
            from audit.services import AuditService
            AuditService.log_error(
                action="refund_data_error",
                message=f"Data error during refund for booking {booking.public_id}: {str(e)}",
                user=cancelled_by,
                error_details={
                    "booking_id": booking.id,
                    "payment_id": payment.id,
                    "error_type": type(e).__name__,
                    "error": str(e),
                }
            )
            raise RefundProcessingError(f"Data error during refund: {str(e)}") from e

    @staticmethod
    def get_refund_amount(booking):
        """
        Calculate refund amount for a booking.

        Args:
            booking: Booking instance

        Returns:
            int: Refund amount in cents, or 0 if no refund
        """
        payment = Payment.objects.filter(
            booking=booking,
            status=STATUS_SUCCEEDED,
            amount_cents__gt=0  # Exclude refunds (negative amounts)
        ).order_by('-created_at').first()

        return payment.amount_cents if payment else 0

    @staticmethod
    def has_been_refunded(booking):
        """
        Check if a booking has been refunded.

        Args:
            booking: Booking instance

        Returns:
            bool: True if refund exists
        """
        return Payment.objects.filter(
            booking=booking,
            amount_cents__lt=0  # Negative = refund
        ).exists()

    @staticmethod
    @transaction.atomic
    def process_emergency_refund(booking, payment_intent_id, reason="overbooking"):
        """
        Process emergency refund for failed confirmations (e.g., overbooking).

        This method bypasses normal validation checks since it's called
        when a payment succeeded but booking confirmation failed.

        Args:
            booking: Booking instance (may be PENDING)
            payment_intent_id: Stripe PaymentIntent ID
            reason: Reason for emergency refund

        Returns:
            tuple: (success: bool, message: str, refund_payment: Payment or None)
        """
        import logging
        logger = logging.getLogger("payments.refund")

        logger.info(f"Processing emergency refund for booking {booking.public_id}, reason: {reason}")

        # Find the successful payment
        payment = Payment.objects.filter(
            booking=booking,
            status=STATUS_SUCCEEDED
        ).order_by('-created_at').first()

        if not payment:
            logger.error(f"No successful payment found for booking {booking.id}")
            return False, "No successful payment found for this booking", None

        # If zero amount (free booking), skip refund
        if booking.amount_cents == 0:
            logger.info("Zero amount booking, no refund needed")
            return True, "Free booking (no refund needed)", None

        # Check if already refunded
        if payment.amount_cents <= 0:
            logger.warning(f"Payment {payment.id} already refunded")
            return False, "Payment already refunded", payment

        # Process Stripe refund (NO validation checks)
        RefundService._initialize_stripe()

        if not payment_intent_id:
            logger.error(f"Payment {payment.id} has no payment_intent_id")
            return False, "Payment has no payment_intent_id - cannot refund", None

        try:
            # Create Stripe refund
            refund = stripe.Refund.create(
                payment_intent=payment_intent_id,
                metadata={
                    "booking_public_id": str(booking.public_id),
                    "reason": reason,
                    "emergency_refund": "true",
                },
            )

            logger.info(f"Stripe refund created: {refund.id}")

            # Ensure currency is valid 3-letter code
            currency = str(payment.currency).upper().strip()[:3] if payment.currency else "EUR"

            # Create refund payment record (negative amount)
            refund_payment = Payment.objects.create(
                user=payment.user,
                booking=booking,
                amount_cents=-abs(payment.amount_cents),  # Negative for refund
                currency=currency,
                status=STATUS_SUCCEEDED,
                stripe_payment_intent_id=payment_intent_id,
                raw_event={
                    "type": "emergency_refund",
                    "refund_id": str(refund.id),
                    "reason": reason,
                    "amount": int(getattr(refund, "amount", 0)) if hasattr(refund, "amount") else 0,
                    "status": str(getattr(refund, "status", "")),
                },
            )

            logger.info(f"Refund payment created: {refund_payment.id}")

            # Log refund
            from audit.services import AuditService

            AuditService.log_payment_refunded(
                refund_payment,
                booking.user,
                amount_cents=payment.amount_cents,
                refund_id=refund.id,
                reason=f"Emergency refund: {reason}"
            )

            return True, f"Emergency refund processed: {refund.id}", refund_payment

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error during emergency refund: {str(e)}")
            return False, f"Stripe error: {str(e)}", None

        except Exception as e:
            logger.error(f"Exception during emergency refund: {str(e)}")
            return False, f"Unexpected error: {str(e)}", None
