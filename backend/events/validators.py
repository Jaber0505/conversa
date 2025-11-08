"""
Event validation logic.

Validators for event business rules including capacity and timing.
"""

from datetime import timedelta
from django.core.exceptions import ValidationError
from django.utils import timezone

from common.constants import (
    MIN_PARTICIPANTS_PER_EVENT as MIN_PARTICIPANTS,
    MAX_PARTICIPANTS_PER_EVENT as MAX_PARTICIPANTS,
    DEFAULT_EVENT_DURATION_HOURS,
)
from common.validators.date_validators import (
    validate_future_datetime,
    validate_reasonable_future,
    validate_business_hours,
)


def validate_event_datetime(value):
    """
    Comprehensive validation for event datetime.

    Business Rules:
    - Must be at least 3h in advance
    - Cannot be more than 7 days in future
    - Event start time within business hours (12h-21h inclus)

    Args:
        value: DateTime to validate

    Raises:
        ValidationError: If datetime doesn't meet requirements
    """
    validate_future_datetime(value)  # 3h minimum advance
    validate_reasonable_future(value)  # Max 7 days in future
    # Business hours rule: 12:00 through 21:00 inclusive (exact at 21:00)
    # Accept if:
    #  - hour in 13..20 (any minutes)
    #  - hour == 12 (any minutes)
    #  - hour == 21 only when minutes==seconds==microseconds==0
    h = value.hour
    if not (
        (12 <= h <= 20)
        or (h == 21 and value.minute == 0 and value.second == 0 and value.microsecond == 0)
    ):
        from django.core.exceptions import ValidationError
        raise ValidationError("Events must be scheduled between 12:00 and 21:00.")


# Event creation time window removed - users can create events 24/7


# validate_max_participants() removed - max_participants field no longer exists
# Event capacity is now dynamically calculated based on partner capacity


def validate_partner_capacity(partner, datetime_start, duration_hours=None, exclude_event_id=None):
    """
    Validate partner has sufficient capacity for creating an event.

    Business Rule:
        Partner must have at least MIN_PARTICIPANTS_PER_EVENT (3) available slots
        on the requested time slot for the event to be created.

        Multiple events can occur simultaneously at the same partner venue,
        as long as the partner has available capacity.

    Example:
        Partner capacity: 50 seats
        18:00-19:00 → Event A (12 confirmed bookings) = 12/50 used
        → Available: 38 seats
        → Can create new event? YES (38 >= 3 minimum required)

        18:00-19:00 → Events using 48/50 seats
        → Available: 2 seats
        → Can create new event? NO (2 < 3 minimum required)

    Args:
        partner: Partner instance
        datetime_start: Proposed event start datetime
        duration_hours: Event duration (defaults to DEFAULT_EVENT_DURATION_HOURS)
        exclude_event_id: Event ID to exclude from calculation (for updates)

    Raises:
        ValidationError: If available capacity < minimum required (3)
    """
    if duration_hours is None:
        duration_hours = DEFAULT_EVENT_DURATION_HOURS

    datetime_end = datetime_start + timedelta(hours=duration_hours)

    # Calculate available capacity for this time slot based on event reservations
    # (sum of max_participants across overlapping active events)
    from partners.services import PartnerService
    available = PartnerService.get_available_capacity_by_reservations(
        partner, datetime_start, datetime_end, exclude_event_id=exclude_event_id
    )

    # If updating an existing event, add back its current bookings
    if exclude_event_id:
        from events.models import Event
        from bookings.models import BookingStatus
        try:
            existing_event = Event.objects.get(id=exclude_event_id)
            # Calculate existing event end time (consistent with duration_hours parameter)
            # NOTE: existing_event.datetime_end uses DEFAULT_EVENT_DURATION_HOURS
            # We use it here for consistency with current implementation
            existing_event_end = existing_event.datetime_end

            # Check if existing event overlaps with the new time slot
            if (existing_event.datetime_start < datetime_end and
                existing_event_end > datetime_start):
                # Add back the number of confirmed bookings
                confirmed_bookings = existing_event.bookings.filter(
                    status=BookingStatus.CONFIRMED
                ).count()
                available += confirmed_bookings
        except Event.DoesNotExist:
            pass

    # Validate minimum capacity requirement
    if available < MIN_PARTICIPANTS:
        raise ValidationError(
            f"Partner '{partner.name}' has insufficient capacity for this time slot. "
            f"Available: {available} seats, Minimum required: {MIN_PARTICIPANTS} seats."
        )


def validate_event_duration(datetime_start, datetime_end):
    """
    Validate event duration is exactly 1 hour.

    Business Rule:
        All events must be exactly 1 hour long (no more, no less).

    Args:
        datetime_start: Event start datetime
        datetime_end: Event end datetime

    Raises:
        ValidationError: If duration is not exactly 1 hour
    """
    duration = datetime_end - datetime_start
    expected_duration = timedelta(hours=1)

    if duration != expected_duration:
        raise ValidationError(
            f"Event duration must be exactly 1 hour. "
            f"Got: {duration.total_seconds() / 3600:.2f} hours."
        )
