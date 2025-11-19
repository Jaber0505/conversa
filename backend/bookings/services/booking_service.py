"""
Booking business logic service.

Handles booking creation, validation, cancellation, and expiration.
"""

from datetime import timedelta
from django.db import transaction
from django.utils import timezone

from common.services.base import BaseService
from common.constants import BOOKING_TTL_MINUTES, CANCELLATION_DEADLINE_HOURS
from common.exceptions import (
    BookingExpiredError,
    BookingAlreadyConfirmedError,
    CancellationDeadlineError,
    EventFullError,
)
from ..validators import validate_cancellation_deadline, validate_event_capacity, validate_event_not_cancelled


class BookingService(BaseService):
    """Service layer for Booking business logic."""

    @staticmethod
    @transaction.atomic
    def create_booking(user, event, amount_cents=None):
        """
        Create a new booking for a user, or return existing PENDING booking.

        Business Rules:
            - If a PENDING booking exists for this user/event, return it (reuse)
            - If a CONFIRMED booking exists, raise ValidationError (only 1 active booking allowed)
            - Otherwise, create a new PENDING booking

        Args:
            user: User making the booking
            event: Event to book
            amount_cents: Booking amount (defaults to event price)

        Returns:
            Booking: Created or existing booking instance

        Raises:
            EventFullError: If event is at capacity
            ValidationError: If user already has a CONFIRMED booking for this event
        """
        from bookings.models import Booking, BookingStatus
        from django.core.exceptions import ValidationError

        # Validate event is not cancelled
        validate_event_not_cancelled(event)

        # Check if user already has an active booking for this event
        existing_booking = Booking.objects.filter(
            user=user,
            event=event
        ).exclude(status=BookingStatus.CANCELLED).first()

        if existing_booking:
            # If PENDING, return it (reuse)
            if existing_booking.status == BookingStatus.PENDING:
                # Refresh expiration time
                existing_booking.expires_at = timezone.now() + timedelta(minutes=BOOKING_TTL_MINUTES)
                existing_booking.save(update_fields=['expires_at', 'updated_at'])
                return existing_booking

            # If CONFIRMED, user cannot create another booking
            elif existing_booking.status == BookingStatus.CONFIRMED:
                raise ValidationError(
                    "You already have a confirmed booking for this event. "
                    "Please cancel it first if you want to create a new one."
                )

        # Validate event capacity (only for new bookings)
        validate_event_capacity(event)

        # Default amount to event price
        if amount_cents is None:
            amount_cents = event.price_cents

        # Calculate expiration
        expires_at = timezone.now() + timedelta(minutes=BOOKING_TTL_MINUTES)

        # Create booking
        # NOTE: Currency hardcoded to EUR for MVP (Belgian/French market)
        # TODO: Support multi-currency when expanding internationally
        booking = Booking.objects.create(
            user=user,
            event=event,
            amount_cents=amount_cents,
            currency="EUR",  # Hardcoded - matches settings.STRIPE_CURRENCY
            expires_at=expires_at
        )

        return booking

    @staticmethod
    @transaction.atomic
    def cancel_booking(booking, cancelled_by=None, system_cancellation=False):
        """
        Cancel a booking if allowed.

        Business Rules:
            - PENDING bookings can always be cancelled
            - CONFIRMED bookings can be cancelled up to 3h before event start
            - CONFIRMED bookings trigger automatic Stripe refund
            - System cancellations (e.g., auto-cancel) bypass deadline check

        Args:
            booking: Booking to cancel
            cancelled_by: User cancelling the booking (defaults to booking.user, None for system)
            system_cancellation: If True, bypass cancellation deadline (for auto-cancel)

        Returns:
            dict: Cancellation result with refund info (if applicable)

        Raises:
            CancellationDeadlineError: If within 3h of event start (unless system_cancellation)
            ValidationError: If refund fails
        """
        from bookings.models import BookingStatus

        # Check cancellation deadline (skip for system cancellations like auto-cancel)
        if not system_cancellation:
            validate_cancellation_deadline(booking)

        cancelled_by = cancelled_by or booking.user
        result = {"cancelled": False, "refunded": False, "refund_message": None}

        # If CONFIRMED, process refund first
        if booking.status == BookingStatus.CONFIRMED:
            from payments.services import RefundService
            from payments.exceptions import (
                PaymentIntentMissingError,
                RefundProcessingError,
                StripeError as PaymentStripeError,
            )
            from django.core.exceptions import ValidationError

            try:
                success, message, refund_payment = RefundService.process_refund(
                    booking=booking,
                    cancelled_by=cancelled_by
                )
                if not success:
                    raise ValidationError(f"Refund failed: {message}")

                result["refunded"] = True
                result["refund_message"] = message
                result["refund_payment_id"] = refund_payment.id if refund_payment else None

            except PaymentIntentMissingError as e:
                # Payment has no payment_intent_id - cannot refund
                raise ValidationError(f"Cannot refund: {str(e)}")

            except PaymentStripeError as e:
                # Stripe API error - cannot complete refund
                raise ValidationError(f"Stripe error: {str(e)}")

            except RefundProcessingError as e:
                # Data processing error during refund
                raise ValidationError(f"Refund processing error: {str(e)}")

            except ValidationError:
                # Re-raise validation errors as-is
                raise

        # Perform cancellation
        booking.mark_cancelled()
        result["cancelled"] = True

        return result

    @staticmethod
    def auto_expire_bookings():
        """
        Automatically expire pending bookings past their expiration time.

        Returns:
            int: Number of bookings expired
        """
        from bookings.models import Booking, BookingStatus

        now = timezone.now()
        expired_bookings = Booking.objects.filter(
            status=BookingStatus.PENDING,
            expires_at__lte=now
        )

        count = expired_bookings.count()
        expired_bookings.update(
            status=BookingStatus.CANCELLED,
            cancelled_at=now,
            updated_at=now
        )

        return count

    @staticmethod
    @transaction.atomic
    def confirm_booking(booking, payment_intent_id=None):
        """
        Confirm a booking after successful payment.

        Business Rules:
            - Validates event capacity before confirmation (prevents overbooking)
            - Checks if booking has expired
            - Publishes event if this is organizer's booking

        Args:
            booking: Booking to confirm
            payment_intent_id: Stripe payment intent ID

        Raises:
            BookingExpiredError: If booking has expired
            ValidationError: If event is full (race condition protection)
        """
        from bookings.models import BookingStatus
        from django.core.exceptions import ValidationError

        # Check if expired
        if booking.status == BookingStatus.PENDING and booking.is_expired:
            raise BookingExpiredError()

        # CRITICAL: Validate capacity before confirmation to prevent overbooking
        # This protects against race conditions where multiple users pay simultaneously
        validate_event_capacity(booking.event)

        # Mark as confirmed
        late = booking.is_expired
        booking.mark_confirmed(payment_intent_id=payment_intent_id, late=late)

        # Publish event if organizer's booking
        if booking.event.organizer_id == booking.user_id:
            if booking.event.status != booking.event.Status.PUBLISHED:
                booking.event.mark_published()

        return booking

    @staticmethod
    def get_user_bookings(user, status=None, event_id=None):
        """
        Get bookings for a specific user with optional filters.

        Args:
            user: User whose bookings to retrieve
            status: Optional status filter
            event_id: Optional event ID filter

        Returns:
            QuerySet: Filtered bookings
        """
        from bookings.models import Booking

        queryset = Booking.objects.filter(user=user).select_related('event')

        if status:
            queryset = queryset.filter(status=status)

        if event_id:
            queryset = queryset.filter(event_id=event_id)

        return queryset.order_by('-created_at')

    @staticmethod
    def can_cancel_booking(booking):
        """
        Check if booking can be cancelled.

        Business Rules:
            - Both PENDING and CONFIRMED can be cancelled
            - Cannot cancel within 3h of event start

        Args:
            booking: Booking to check

        Returns:
            tuple: (bool, str) - (can_cancel, reason_if_not)
        """
        from bookings.models import BookingStatus

        # Already cancelled bookings cannot be cancelled again
        if booking.status == BookingStatus.CANCELLED:
            return False, "Booking is already cancelled"

        # Check deadline (3h before event)
        deadline = booking.event.datetime_start - timedelta(
            hours=CANCELLATION_DEADLINE_HOURS
        )
        if timezone.now() >= deadline:
            return False, f"Cannot cancel within {CANCELLATION_DEADLINE_HOURS}h of event"

        return True, ""
