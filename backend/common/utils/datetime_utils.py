"""
DateTime utility functions.

Helper functions for common datetime operations across the application.
"""

from datetime import timedelta
from django.utils import timezone


def is_within_hours(target_datetime, hours):
    """
    Check if target datetime is within specified hours from now.

    Args:
        target_datetime: DateTime to check
        hours: Number of hours threshold

    Returns:
        bool: True if within threshold, False otherwise
    """
    threshold = timezone.now() + timedelta(hours=hours)
    return target_datetime <= threshold


def time_until(target_datetime):
    """
    Calculate time remaining until target datetime.

    Args:
        target_datetime: Target datetime

    Returns:
        timedelta: Time remaining (negative if in the past)
    """
    return target_datetime - timezone.now()


def is_same_day(dt1, dt2):
    """
    Check if two datetimes are on the same calendar day.

    Args:
        dt1: First datetime
        dt2: Second datetime

    Returns:
        bool: True if same day, False otherwise
    """
    return dt1.date() == dt2.date()


def get_date_range(start_date, end_date):
    """
    Generate list of dates between start and end (inclusive).

    Args:
        start_date: Start date
        end_date: End date

    Returns:
        list: List of dates
    """
    delta = end_date - start_date
    return [start_date + timedelta(days=i) for i in range(delta.days + 1)]
