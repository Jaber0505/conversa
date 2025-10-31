"""
Tests for common validators.

These tests ensure date validators work correctly for business rules.
"""

from datetime import timedelta
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone

from common.validators.date_validators import (
    validate_future_datetime,
    validate_reasonable_future,
    validate_business_hours,
)


class DateValidatorsTestCase(TestCase):
    """Test suite for date validation functions."""

    def test_validate_future_datetime_accepts_future_dates(self):
        """Should accept datetime more than 24 hours in future (event requirement)."""
        future_dt = timezone.now() + timedelta(hours=25)
        try:
            validate_future_datetime(future_dt)
        except ValidationError:
            self.fail("validate_future_datetime raised ValidationError unexpectedly")

    def test_validate_future_datetime_rejects_past_dates(self):
        """Should reject datetime in the past."""
        past_dt = timezone.now() - timedelta(hours=1)
        with self.assertRaises(ValidationError):
            validate_future_datetime(past_dt)

    def test_validate_future_datetime_requires_minimum_notice(self):
        """Should reject datetime less than 24 hours in future."""
        near_future = timezone.now() + timedelta(hours=1)
        with self.assertRaises(ValidationError):
            validate_future_datetime(near_future)

    def test_validate_reasonable_future_accepts_within_range(self):
        """Should accept datetime within max range (7 days for events)."""
        # Use 5 days to be safely within the 7-day limit
        future_dt = timezone.now() + timedelta(days=5)
        try:
            validate_reasonable_future(future_dt)
        except ValidationError:
            self.fail("validate_reasonable_future raised ValidationError unexpectedly")

    def test_validate_reasonable_future_rejects_too_far(self):
        """Should reject datetime more than 365 days in future."""
        far_future = timezone.now() + timedelta(days=400)
        with self.assertRaises(ValidationError):
            validate_reasonable_future(far_future)

    def test_validate_business_hours_accepts_valid_hours(self):
        """Should accept datetime during business hours (default 8am-11pm)."""
        # Create datetime at 2pm (14:00) - valid for any business hours range
        valid_time = timezone.now().replace(hour=14, minute=0, second=0, microsecond=0)
        try:
            validate_business_hours(valid_time, start_hour=8, end_hour=23)
        except ValidationError:
            self.fail("validate_business_hours raised ValidationError unexpectedly")

    def test_validate_business_hours_rejects_too_early(self):
        """Should reject datetime before start_hour (8am default)."""
        too_early = timezone.now().replace(hour=6, minute=0, second=0, microsecond=0)
        with self.assertRaises(ValidationError):
            validate_business_hours(too_early, start_hour=8, end_hour=23)

    def test_validate_business_hours_rejects_too_late(self):
        """Should reject datetime at or after end_hour (11pm default)."""
        too_late = timezone.now().replace(hour=23, minute=30, second=0, microsecond=0)
        with self.assertRaises(ValidationError):
            validate_business_hours(too_late, start_hour=8, end_hour=23)
