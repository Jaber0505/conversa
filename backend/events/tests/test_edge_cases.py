"""
Edge case tests for Events module.

Tests boundary conditions and validation rules.
"""

from datetime import timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from languages.models import Language
from partners.models import Partner
from events.models import Event
from events.validators import (
    validate_event_datetime,
    validate_partner_capacity,
)
from events.services import EventService
from bookings.models import Booking, BookingStatus

User = get_user_model()


class EventDatetimeEdgeCasesTest(TestCase):
    """Test edge cases for event datetime validation."""

    def setUp(self):
        """Create test fixtures."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            age=25,
            consent_given=True,
        )
        self.language = Language.objects.create(
            code="fr",
            label_fr="Français",
            label_en="French",
            label_nl="Frans",
            is_active=True,
        )
        self.partner = Partner.objects.create(
            name="Test Bar",
            address="123 Test St",
            city="Brussels",
            capacity=50,
            is_active=True,
        )

    def test_event_before_12h_should_fail(self):
        """Event at 11:59 should fail (before 12:00 business hours)."""
        now = timezone.now()
        # Create datetime at 11:59
        event_time = now.replace(hour=11, minute=59, second=0, microsecond=0) + timedelta(days=2)

        with self.assertRaises(ValidationError) as cm:
            validate_event_datetime(event_time)

        self.assertIn("business hours", str(cm.exception).lower())

    def test_event_after_21h_should_fail(self):
        """Event at 21:01 should fail (after 21:00 business hours)."""
        now = timezone.now()
        # Create datetime at 21:01
        event_time = now.replace(hour=21, minute=1, second=0, microsecond=0) + timedelta(days=2)

        with self.assertRaises(ValidationError) as cm:
            validate_event_datetime(event_time)

        self.assertIn("business hours", str(cm.exception).lower())

    def test_event_at_12h_exactly_should_pass(self):
        """Event at 12:00 exactly should pass (start of business hours)."""
        now = timezone.now()
        # Create datetime at 12:00
        event_time = now.replace(hour=12, minute=0, second=0, microsecond=0) + timedelta(days=2)

        # Should not raise
        validate_event_datetime(event_time)

    def test_event_at_21h_exactly_should_pass(self):
        """Event at 21:00 exactly should pass (end of business hours)."""
        now = timezone.now()
        # Create datetime at 21:00
        event_time = now.replace(hour=21, minute=0, second=0, microsecond=0) + timedelta(days=2)

        # Should not raise
        validate_event_datetime(event_time)

    def test_event_in_23_hours_should_fail(self):
        """Event in 23 hours should fail (need 24h minimum advance)."""
        event_time = timezone.now() + timedelta(hours=23)

        with self.assertRaises(ValidationError) as cm:
            validate_event_datetime(event_time)

        self.assertIn("24", str(cm.exception))

    def test_event_in_24_hours_exactly_should_pass(self):
        """Event in 24 hours exactly should pass (minimum advance)."""
        event_time = timezone.now() + timedelta(hours=24, minutes=1)
        # Adjust to business hours (12h-21h)
        event_time = event_time.replace(hour=14, minute=0, second=0, microsecond=0)

        # Should not raise
        validate_event_datetime(event_time)

    def test_event_in_8_days_should_fail(self):
        """Event in 8 days should fail (max 7 days future)."""
        event_time = timezone.now() + timedelta(days=8)
        # Adjust to business hours
        event_time = event_time.replace(hour=14, minute=0, second=0, microsecond=0)

        with self.assertRaises(ValidationError) as cm:
            validate_event_datetime(event_time)

        self.assertIn("7 days", str(cm.exception))

    def test_event_in_7_days_exactly_should_pass(self):
        """Event in 7 days exactly should pass (max future)."""
        event_time = timezone.now() + timedelta(days=7)
        # Adjust to business hours
        event_time = event_time.replace(hour=14, minute=0, second=0, microsecond=0)

        # Should not raise
        validate_event_datetime(event_time)

    def test_event_in_past_should_fail(self):
        """Event in the past should fail."""
        event_time = timezone.now() - timedelta(hours=1)

        with self.assertRaises(ValidationError) as cm:
            validate_event_datetime(event_time)

        self.assertIn("future", str(cm.exception).lower())


class PartnerCapacityEdgeCasesTest(TestCase):
    """Test edge cases for partner capacity validation."""

    def setUp(self):
        """Create test fixtures."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            age=25,
            consent_given=True,
        )
        self.language = Language.objects.create(
            code="fr",
            label_fr="Français",
            label_en="French",
            label_nl="Frans",
            is_active=True,
        )

    def test_partner_capacity_2_should_fail(self):
        """Partner with capacity=2 should fail (need min 3)."""
        partner = Partner.objects.create(
            name="Tiny Bar",
            address="123 Test St",
            city="Brussels",
            capacity=2,  # Below minimum
            is_active=True,
        )

        datetime_start = timezone.now() + timedelta(days=2)
        datetime_start = datetime_start.replace(hour=14, minute=0, second=0, microsecond=0)

        with self.assertRaises(ValidationError) as cm:
            validate_partner_capacity(partner, datetime_start)

        self.assertIn("insufficient capacity", str(cm.exception).lower())
        self.assertIn("2", str(cm.exception))
        self.assertIn("3", str(cm.exception))

    def test_partner_capacity_3_exactly_should_pass(self):
        """Partner with capacity=3 exactly should pass (minimum)."""
        partner = Partner.objects.create(
            name="Small Bar",
            address="123 Test St",
            city="Brussels",
            capacity=3,  # Exactly minimum
            is_active=True,
        )

        datetime_start = timezone.now() + timedelta(days=2)
        datetime_start = datetime_start.replace(hour=14, minute=0, second=0, microsecond=0)

        # Should not raise
        validate_partner_capacity(partner, datetime_start)

    def test_partner_with_48_bookings_leaving_2_available_should_fail(self):
        """Partner with 48/50 bookings (2 available) should fail (need 3)."""
        partner = Partner.objects.create(
            name="Busy Bar",
            address="123 Test St",
            city="Brussels",
            capacity=50,
            is_active=True,
        )

        # Create existing event with 48 confirmed bookings
        existing_event = Event.objects.create(
            organizer=self.user,
            partner=partner,
            language=self.language,
            theme="Existing Event",
            difficulty="easy",
            datetime_start=timezone.now() + timedelta(days=2, hours=14),
            status="PUBLISHED",
        )

        # Create 48 confirmed bookings
        for i in range(48):
            user = User.objects.create_user(
                email=f"user{i}@example.com",
                password="pass",
                age=20,
                consent_given=True,
            )
            Booking.objects.create(
                user=user,
                event=existing_event,
                amount_cents=700,
                status=BookingStatus.CONFIRMED,
            )

        # Try to create new event at overlapping time
        datetime_start = existing_event.datetime_start + timedelta(minutes=30)

        with self.assertRaises(ValidationError) as cm:
            validate_partner_capacity(partner, datetime_start)

        self.assertIn("insufficient capacity", str(cm.exception).lower())

    def test_partner_with_47_bookings_leaving_3_available_should_pass(self):
        """Partner with 47/50 bookings (3 available) should pass (exactly minimum)."""
        partner = Partner.objects.create(
            name="Almost Full Bar",
            address="123 Test St",
            city="Brussels",
            capacity=50,
            is_active=True,
        )

        # Create existing event with 47 confirmed bookings
        existing_event = Event.objects.create(
            organizer=self.user,
            partner=partner,
            language=self.language,
            theme="Existing Event",
            difficulty="easy",
            datetime_start=timezone.now() + timedelta(days=2, hours=14),
            status="PUBLISHED",
        )

        # Create 47 confirmed bookings
        for i in range(47):
            user = User.objects.create_user(
                email=f"user{i}@example.com",
                password="pass",
                age=20,
                consent_given=True,
            )
            Booking.objects.create(
                user=user,
                event=existing_event,
                amount_cents=700,
                status=BookingStatus.CONFIRMED,
            )

        # Try to create new event at overlapping time
        datetime_start = existing_event.datetime_start + timedelta(minutes=30)

        # Should not raise (exactly 3 available)
        validate_partner_capacity(partner, datetime_start)


class EventServiceEdgeCasesTest(TestCase):
    """Test edge cases for EventService."""

    def setUp(self):
        """Create test fixtures."""
        self.user = User.objects.create_user(
            email="organizer@example.com",
            password="testpass123",
            age=25,
            consent_given=True,
        )
        self.language = Language.objects.create(
            code="fr",
            label_fr="Français",
            label_en="French",
            label_nl="Frans",
            is_active=True,
        )
        self.partner = Partner.objects.create(
            name="Test Bar",
            address="123 Test St",
            city="Brussels",
            capacity=50,
            is_active=True,
        )

    def test_create_event_with_all_boundary_conditions(self):
        """Create event with all validations at boundaries should succeed."""
        # Event at 12:00 (start of business hours)
        # In exactly 24 hours (minimum advance)
        # Partner capacity = 3 (minimum)
        # In 7 days (maximum future)

        partner_min = Partner.objects.create(
            name="Min Capacity Bar",
            address="456 Test St",
            city="Brussels",
            capacity=3,  # Minimum
            is_active=True,
        )

        # Create datetime: 7 days in future at 12:00
        datetime_start = timezone.now() + timedelta(days=7)
        datetime_start = datetime_start.replace(hour=12, minute=0, second=0, microsecond=0)

        event, booking = EventService.create_event_with_organizer_booking(
            organizer=self.user,
            partner=partner_min,
            language=self.language,
            theme="Boundary Test Event",
            difficulty="easy",
            datetime_start=datetime_start,
        )

        self.assertIsNotNone(event)
        self.assertEqual(event.status, "DRAFT")
        self.assertIsNotNone(booking)
        self.assertEqual(booking.status, BookingStatus.PENDING)

    def test_create_event_multiple_simultaneous_events_same_partner(self):
        """Multiple events at same time should work if capacity allows."""
        datetime_start = timezone.now() + timedelta(days=2)
        datetime_start = datetime_start.replace(hour=14, minute=0, second=0, microsecond=0)

        # Create first event
        event1, _ = EventService.create_event_with_organizer_booking(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="Event 1",
            difficulty="easy",
            datetime_start=datetime_start,
        )

        # Create 10 confirmed bookings for event1
        for i in range(10):
            user = User.objects.create_user(
                email=f"user{i}@example.com",
                password="pass",
                age=20,
                consent_given=True,
            )
            Booking.objects.create(
                user=user,
                event=event1,
                amount_cents=700,
                status=BookingStatus.CONFIRMED,
            )

        # Publish event1
        event1.status = "PUBLISHED"
        event1.save()

        # Create second organizer
        organizer2 = User.objects.create_user(
            email="organizer2@example.com",
            password="pass",
            age=25,
            consent_given=True,
        )

        # Create second event at exact same time (should succeed - capacity allows)
        event2, booking2 = EventService.create_event_with_organizer_booking(
            organizer=organizer2,
            partner=self.partner,
            language=self.language,
            theme="Event 2",
            difficulty="easy",
            datetime_start=datetime_start,  # Same time!
        )

        self.assertIsNotNone(event2)
        # Should work because partner has 50 capacity, event1 uses ~10, leaving 40+
