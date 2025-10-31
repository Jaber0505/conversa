"""
Tests for EventService business logic.

These tests ensure that event creation, validation, and cancellation
work correctly according to business rules.
"""

from datetime import timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from languages.models import Language
from partners.models import Partner
from events.models import Event
from events.services import EventService
from bookings.models import Booking, BookingStatus

User = get_user_model()


class EventServiceTestCase(TestCase):
    """Test suite for EventService."""

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

    def test_create_event_with_organizer_booking(self):
        """Should create event and auto-create organizer booking."""
        # Create event for 2 days from now at 14:00 (2 PM) - at least 24h+ in advance
        two_days_2pm = (timezone.now() + timedelta(days=2)).replace(hour=14, minute=0, second=0, microsecond=0)

        event_data = {
            "partner": self.partner,
            "language": self.language,
            "theme": "Test Event",
            "difficulty": "easy",
            "datetime_start": two_days_2pm,
        }

        event, booking = EventService.create_event_with_organizer_booking(
            organizer=self.user,
            event_data=event_data,
        )

        # Check event was created
        self.assertEqual(event.organizer, self.user)
        self.assertEqual(event.status, Event.Status.DRAFT)
        self.assertEqual(event.theme, "Test Event")

        # Check organizer booking was created
        self.assertEqual(booking.user, self.user)
        self.assertEqual(booking.event, event)
        self.assertEqual(booking.status, BookingStatus.PENDING)
        self.assertEqual(booking.amount_cents, event.price_cents)

    def test_cancel_event_cascades_to_bookings(self):
        """Should cancel event and all associated bookings."""
        # Create event for 2 days from now at 18:00 (6 PM)
        two_days_6pm = (timezone.now() + timedelta(days=2)).replace(hour=18, minute=0, second=0, microsecond=0)

        event = Event.objects.create(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="To Cancel",
            difficulty="easy",
            datetime_start=two_days_6pm,
            status=Event.Status.PUBLISHED,
        )

        # Create confirmed bookings
        Booking.objects.create(
            user=self.user,
            event=event,
            amount_cents=700,
            status=BookingStatus.CONFIRMED,
        )

        # Cancel event
        EventService.cancel_event(event=event, cancelled_by=self.user)

        # Check event is cancelled
        event.refresh_from_db()
        self.assertEqual(event.status, Event.Status.CANCELLED)

        # Check all bookings are cancelled
        bookings = Booking.objects.filter(event=event)
        for booking in bookings:
            self.assertEqual(booking.status, BookingStatus.CANCELLED)

    def test_check_and_cancel_underpopulated_events(self):
        """Should auto-cancel events with < 3 participants 1h before start."""
        # Create event starting in 30 minutes
        event = Event.objects.create(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="Underpopulated",
            difficulty="easy",
            datetime_start=timezone.now() + timedelta(minutes=30),
            status=Event.Status.PUBLISHED,
        )

        # Create only 2 confirmed bookings (less than min 3)
        Booking.objects.create(
            user=self.user,
            event=event,
            amount_cents=700,
            status=BookingStatus.CONFIRMED,
        )

        # Run auto-cancellation check
        cancelled = EventService.check_and_cancel_underpopulated_events()

        # Event should be cancelled
        self.assertEqual(len(cancelled), 1)
        self.assertEqual(cancelled[0].id, event.id)

        event.refresh_from_db()
        self.assertEqual(event.status, Event.Status.CANCELLED)

    def test_is_event_full(self):
        """Should correctly identify when event is full based on partner capacity."""
        # Create event for 2 days from now at 20:00 (8 PM)
        two_days_8pm = (timezone.now() + timedelta(days=2)).replace(hour=20, minute=0, second=0, microsecond=0)

        # Create small partner with only 5 capacity for testing
        small_partner = Partner.objects.create(
            name="Small Venue",
            address="456 Small St",
            city="Brussels",
            capacity=5,  # Small capacity
            is_active=True,
        )

        event = Event.objects.create(
            organizer=self.user,
            partner=small_partner,
            language=self.language,
            theme="Full Event",
            difficulty="easy",
            datetime_start=two_days_8pm,
            status=Event.Status.PUBLISHED,
        )

        # Initially not full (5 slots available)
        self.assertFalse(EventService.is_event_full(event))

        # Add 5 confirmed bookings to fill all partner capacity
        for i in range(5):
            user = User.objects.create_user(
                email=f"user{i}@example.com",
                password="pass",
                age=20,
                consent_given=True,
            )
            Booking.objects.create(
                user=user,
                event=event,
                amount_cents=700,
                status=BookingStatus.CONFIRMED,
            )

        # Now should be full (0 available capacity)
        self.assertTrue(EventService.is_event_full(event))
