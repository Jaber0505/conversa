"""
Date and time validation utilities.

Validators for ensuring dates are in the future, within acceptable ranges,
and conform to business rules.
"""

from datetime import timedelta
from django.core.exceptions import ValidationError
from django.utils import timezone

from common.constants import (
    MIN_ADVANCE_BOOKING_HOURS,
    MAX_FUTURE_BOOKING_DAYS,
)


def validate_future_datetime(value):
    """
    Validate that datetime is in the future with minimum advance notice.

    Business Rules:
    - Event must be at least MIN_ADVANCE_BOOKING_HOURS (3h) in advance

    Args:
        value: DateTime to validate

    Raises:
        ValidationError: If datetime is in the past or too close to now
    """
    now = timezone.now()

    if value <= now:
        raise ValidationError("Event datetime must be in the future.")

    # Require minimum advance notice (3 hours)
    min_notice = now + timedelta(hours=MIN_ADVANCE_BOOKING_HOURS)
    if value < min_notice:
        raise ValidationError(
            f"Impossible de créer : délai inférieur à {MIN_ADVANCE_BOOKING_HOURS} heures."
        )


def validate_reasonable_future(value, max_days=None):
    """
    Validate that datetime is not too far in the future.

    Business Rule:
    - Events cannot be scheduled more than MAX_FUTURE_BOOKING_DAYS (7 days) in advance

    Args:
        value: DateTime to validate
        max_days: Maximum days in the future (default from constants: 7 days)

    Raises:
        ValidationError: If datetime is too far in future
    """
    if max_days is None:
        max_days = MAX_FUTURE_BOOKING_DAYS

    # Allow any time on the Nth day (inclusive by calendar day)
    now = timezone.now()
    max_date = (now + timedelta(days=max_days)).date()
    if value.date() > max_date:
        raise ValidationError(
            f"Events cannot be scheduled more than {max_days} days in advance."
        )


def validate_business_hours(value, start_hour=8, end_hour=23):
    """
    Validate that event time is within business hours.

    Note: This validates when the EVENT STARTS, not when users can CREATE events.
    For event creation time window restrictions, see validate_creation_time_window().

    Args:
        value: DateTime to validate
        start_hour: Earliest allowed hour (default 8am)
        end_hour: Latest allowed hour (default 11pm)

    Raises:
        ValidationError: If time is outside business hours
    """
    hour = value.hour
    if not (start_hour <= hour < end_hour):
        raise ValidationError(
            f"Events must be scheduled between {start_hour}:00 and {end_hour}:00."
        )


# Event creation time window removed - users can create events 24/7
