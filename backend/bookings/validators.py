"""
Booking validation logic.

Validators for booking business rules including cancellation deadlines.
"""

from datetime import timedelta
from django.core.exceptions import ValidationError
from django.utils import timezone

from common.constants import CANCELLATION_DEADLINE_HOURS, MIN_PARTICIPANTS_PER_EVENT, MAX_PARTICIPANTS_PER_EVENT
from common.exceptions import CancellationDeadlineError


def validate_cancellation_deadline(booking):
    """
    Validate that booking can be cancelled.

    Cancellation is not allowed within CANCELLATION_DEADLINE_HOURS (3h) of event start.
    This deadline applies to both PENDING and CONFIRMED bookings.

    Args:
        booking: Booking instance to validate

    Raises:
        CancellationDeadlineError: If within cancellation deadline
    """
    if not booking.event:
        return

    deadline = booking.event.datetime_start - timedelta(hours=CANCELLATION_DEADLINE_HOURS)
    now = timezone.now()

    if now >= deadline:
        raise CancellationDeadlineError(
            f"Cannot cancel booking within {CANCELLATION_DEADLINE_HOURS} hours of event start."
        )


def validate_event_not_cancelled(event):
    """
    Validate that event is not cancelled.

    Args:
        event: Event instance to validate

    Raises:
        ValidationError: If event is cancelled
    """
    from events.models import EventStatus

    if event.status == EventStatus.CANCELLED or event.is_cancelled:
        raise ValidationError("Cannot create or modify booking for a cancelled event.")


def validate_event_not_started(booking):
    """
    Validate that event has not started yet.

    Args:
        booking: Booking instance to validate

    Raises:
        ValidationError: If event has already started
    """
    if not booking.event:
        return

    if timezone.now() >= booking.event.datetime_start:
        raise ValidationError("Cannot modify booking for an event that has already started.")


def validate_event_capacity(event):
    """
    Validate that event has available capacity for booking.

    Business Rules:
        - Only CONFIRMED bookings count towards capacity
        - PENDING bookings do not reserve a spot (payment required first)
        - This prevents unpaid bookings from blocking event capacity

    Args:
        event: Event instance to validate

    Raises:
        ValidationError: If event is full (no available slots)
    """
    # Enforce per-event maximum (6 per event by business rule)
    from bookings.models import BookingStatus
    # Count only CONFIRMED seats - PENDING bookings don't reserve capacity
    # until payment is completed (prevents unpaid bookings from blocking spots)
    confirmed_count = event.bookings.filter(status=BookingStatus.CONFIRMED).count()
    per_event_cap = int(getattr(event, 'max_participants', MAX_PARTICIPANTS_PER_EVENT) or MAX_PARTICIPANTS_PER_EVENT)
    if confirmed_count >= per_event_cap:
        raise ValidationError(
            f"Event is full for this time slot (limit {per_event_cap} per event)."
        )

    # Also ensure partner slot capacity has at least 1 available seat
    available_slots = event.partner.get_available_capacity(event.datetime_start, event.datetime_end)
    if available_slots <= 0:
        raise ValidationError(
            f"Partner '{event.partner.name}' has no available capacity left for this time slot."
        )
