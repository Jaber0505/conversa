"""
Tests for event validators.

Ensures that business rules for event creation and validation
are properly enforced.
"""

from datetime import timedelta
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model
from unittest.mock import patch

from events.validators import (
    validate_event_datetime,
    validate_partner_capacity,
)

User = get_user_model()


class EventDatetimeValidatorTests(TestCase):
    """Test event datetime validation rules."""

    def test_event_must_be_3h_in_advance(self):
        """Event must be scheduled at least 3 hours in advance."""
        # 2 hours from now (too soon)
        too_soon = timezone.now() + timedelta(hours=2)

        with self.assertRaises(ValidationError) as ctx:
            validate_event_datetime(too_soon)

        # Error message mentions a 3-hour minimum
        self.assertIn("3", str(ctx.exception))

    def test_event_cannot_be_more_than_7_days_ahead(self):
        """Event cannot be scheduled more than 7 days in advance."""
        # 8 days from now (too far)
        too_far = timezone.now() + timedelta(days=8)

        with self.assertRaises(ValidationError) as ctx:
            validate_event_datetime(too_far)

        self.assertIn("7 days", str(ctx.exception))

    def test_event_must_be_in_business_hours(self):
        """Event must start between 12pm and 9pm (12h-21h inclusive)."""
        # 2 days from now at 10 AM (outside business hours - too early)
        two_days_10am = (timezone.now() + timedelta(days=2)).replace(
            hour=10, minute=0, second=0, microsecond=0
        )

        with self.assertRaises(ValidationError) as ctx:
            validate_event_datetime(two_days_10am)
        self.assertIn("between 12:00 and 21:00", str(ctx.exception))

    def test_event_after_9pm_not_allowed(self):
        """Event cannot start after 9pm (21:00 inclusive)."""
        # 2 days from now at 10 PM (outside business hours - too late)
        two_days_10pm = (timezone.now() + timedelta(days=2)).replace(
            hour=22, minute=0, second=0, microsecond=0
        )

        with self.assertRaises(ValidationError) as ctx:
            validate_event_datetime(two_days_10pm)
        self.assertIn("between 12:00 and 21:00", str(ctx.exception))

    def test_valid_event_datetime_passes(self):
        """Valid event datetime (≥3h, <7 days, business hours) should pass."""
        # 2 days from now at 14:00 (2 PM) - definitely valid
        two_days_2pm = (timezone.now() + timedelta(days=2)).replace(
            hour=14, minute=0, second=0, microsecond=0
        )

        # Should not raise
        try:
            validate_event_datetime(two_days_2pm)
        except ValidationError as e:
            self.fail(f"Valid datetime raised ValidationError: {e}")

    def test_event_at_21_is_allowed(self):
        """Event starting exactly at 21:00 should be allowed (inclusive)."""
        two_days_9pm = (timezone.now() + timedelta(days=2)).replace(
            hour=21, minute=0, second=0, microsecond=0
        )

        try:
            validate_event_datetime(two_days_9pm)
        except ValidationError as e:
            self.fail(f"21:00 should be valid but raised: {e}")


class PartnerCapacityValidatorTests(TestCase):
    """Test partner capacity validation for event creation."""

    def setUp(self):
        """Set up test fixtures."""
        from partners.models import Partner
        from languages.models import Language
        from events.models import Event
        from users.models import User

        # Create test partner with capacity of 50
        self.partner = Partner.objects.create(
            name="Test Cafe",
            address="123 Test Street",
            city="Brussels",
            capacity=50,
            is_active=True,
        )

        # Create test language
        self.language = Language.objects.create(
            code="fr",
            label_fr="Français",
            label_en="French",
            label_nl="Frans",
            is_active=True,
        )

        # Create test user
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            age=25,
            consent_given=True,
            is_active=True,
        )

    def test_sufficient_capacity_passes(self):
        """Partner with >= 3 available slots should pass validation."""
        # 2 days from now at 14:00
        event_time = (timezone.now() + timedelta(days=2)).replace(
            hour=14, minute=0, second=0, microsecond=0
        )

        # Should not raise (partner has 50 available slots)
        try:
            validate_partner_capacity(self.partner, event_time)
        except ValidationError:
            self.fail("Partner with 50 available slots should pass")

    def test_insufficient_capacity_fails(self):
        """Partner with < 3 available slots should fail validation."""
        from events.models import Event
        from bookings.models import Booking, BookingStatus

        # 2 days from now at 14:00
        event_time = (timezone.now() + timedelta(days=2)).replace(
            hour=14, minute=0, second=0, microsecond=0
        )

        # Create existing event using 48/50 capacity (leaving only 2 slots)
        existing_event = Event.objects.create(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="Test Event",
            difficulty="easy",
            datetime_start=event_time,
            status=Event.Status.PUBLISHED,
        )

        # Create 48 confirmed bookings
        for i in range(48):
            user = User.objects.create_user(
                email=f"participant{i}@example.com",
                password="pass123",
                age=20,
                consent_given=True,
                is_active=True,
            )
            Booking.objects.create(
                user=user,
                event=existing_event,
                status=BookingStatus.CONFIRMED,
                amount_cents=700,
            )

        # Try to create new event at same time (only 2 slots available)
        with self.assertRaises(ValidationError) as ctx:
            validate_partner_capacity(self.partner, event_time)

        self.assertIn("insufficient capacity", str(ctx.exception).lower())
        self.assertIn("2", str(ctx.exception))  # Available slots
        self.assertIn("3", str(ctx.exception))  # Minimum required
