"""
Tests for common utility functions.

These tests ensure datetime utilities work correctly.
"""

from datetime import timedelta, date
from django.test import TestCase
from django.utils import timezone

from common.utils.datetime_utils import (
    is_within_hours,
    time_until,
    is_same_day,
    get_date_range,
)


class DateTimeUtilsTestCase(TestCase):
    """Test suite for datetime utility functions."""

    def test_is_within_hours_true_when_within_threshold(self):
        """Should return True if target is within specified hours."""
        target = timezone.now() + timedelta(hours=5)
        self.assertTrue(is_within_hours(target, hours=10))

    def test_is_within_hours_false_when_beyond_threshold(self):
        """Should return False if target is beyond specified hours."""
        target = timezone.now() + timedelta(hours=15)
        self.assertFalse(is_within_hours(target, hours=10))

    def test_is_within_hours_edge_case_exact_threshold(self):
        """Should return True if exactly at threshold."""
        target = timezone.now() + timedelta(hours=10)
        self.assertTrue(is_within_hours(target, hours=10))

    def test_time_until_returns_positive_for_future(self):
        """Should return positive timedelta for future datetime."""
        target = timezone.now() + timedelta(hours=5)
        result = time_until(target)
        self.assertGreater(result.total_seconds(), 0)

    def test_time_until_returns_negative_for_past(self):
        """Should return negative timedelta for past datetime."""
        target = timezone.now() - timedelta(hours=5)
        result = time_until(target)
        self.assertLess(result.total_seconds(), 0)

    def test_is_same_day_true_for_same_date(self):
        """Should return True for datetimes on same calendar day."""
        dt1 = timezone.now().replace(hour=10, minute=0)
        dt2 = timezone.now().replace(hour=22, minute=0)
        self.assertTrue(is_same_day(dt1, dt2))

    def test_is_same_day_false_for_different_dates(self):
        """Should return False for datetimes on different days."""
        dt1 = timezone.now()
        dt2 = timezone.now() + timedelta(days=1)
        self.assertFalse(is_same_day(dt1, dt2))

    def test_get_date_range_returns_correct_dates(self):
        """Should return list of dates between start and end inclusive."""
        start = date(2025, 1, 1)
        end = date(2025, 1, 5)
        result = get_date_range(start, end)

        self.assertEqual(len(result), 5)
        self.assertEqual(result[0], start)
        self.assertEqual(result[-1], end)

    def test_get_date_range_single_day(self):
        """Should return single date when start equals end."""
        single_day = date(2025, 1, 1)
        result = get_date_range(single_day, single_day)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], single_day)
