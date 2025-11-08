"""
Tests for EventService business logic.

These tests ensure that event creation, validation, and cancellation
work correctly according to business rules.
"""

from datetime import timedelta
from unittest.mock import patch
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
            label_fr="Francais",
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
        # Create event for 2 days from now at 14:00 (2 PM) - well beyond 3h minimum
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

    def test_cancel_event_published_triggers_refunds(self):
        """Cancelling a PUBLISHED event should refund confirmed bookings."""
        # Create event 4 hours from now (beyond 3h deadline)
        four_hours = (timezone.now() + timedelta(hours=4)).replace(minute=0, second=0, microsecond=0)
        event = Event.objects.create(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="Refundable",
            difficulty="easy",
            datetime_start=four_hours,
            status=Event.Status.PUBLISHED,
        )

        # One confirmed and one pending booking
        confirmed = Booking.objects.create(
            user=self.user,
            event=event,
            amount_cents=700,
            status=BookingStatus.CONFIRMED,
        )
        pending = Booking.objects.create(
            user=self.user,
            event=event,
            amount_cents=700,
            status=BookingStatus.PENDING,
        )

        with patch("payments.services.refund_service.RefundService.process_refund", return_value=(True, "ok", None)) as mock_refund:
            EventService.cancel_event(event=event, cancelled_by=self.user)

            # All bookings should be cancelled
            confirmed.refresh_from_db()
            pending.refresh_from_db()
            self.assertEqual(confirmed.status, BookingStatus.CANCELLED)
            self.assertEqual(pending.status, BookingStatus.CANCELLED)

            # Refund should be attempted exactly once (for the confirmed booking)
            self.assertEqual(mock_refund.call_count, 1)

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

    def test_get_total_participants(self):
        """
        Total participants = organizer (1) + confirmed bookings.
        """
        # Create event
        event = Event.objects.create(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="Test Event",
            difficulty="easy",
            datetime_start=timezone.now() + timedelta(hours=4),
            status=Event.Status.PUBLISHED,
        )

        # Initially: only organizer (1 participant)
        total = EventService.get_total_participants(event)
        self.assertEqual(total, 1)  # Organizer only

        # Add a confirmed booking
        other_user = User.objects.create_user(
            email="other@example.com",
            password="testpass123",
            age=25,
            consent_given=True,
        )
        Booking.objects.create(
            user=other_user,
            event=event,
            amount_cents=700,
            status=BookingStatus.CONFIRMED,
        )

        # Now: organizer + 1 booking = 2 participants
        total = EventService.get_total_participants(event)
        self.assertEqual(total, 2)


    def test_get_available_slots(self):
        """
        Available slots = MAX_PARTICIPANTS - (organizer + confirmed bookings).
        """
        from common.constants import MAX_PARTICIPANTS_PER_EVENT

        # Create event
        event = Event.objects.create(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="Test Event",
            difficulty="easy",
            datetime_start=timezone.now() + timedelta(hours=4),
            status=Event.Status.PUBLISHED,
        )

        # Initially: 5 slots available (6 max - 1 organizer)
        available = EventService.get_available_slots(event)
        self.assertEqual(available, MAX_PARTICIPANTS_PER_EVENT - 1)

        # Add 2 confirmed bookings
        for i in range(2):
            user = User.objects.create_user(
                email=f"user{i}@test.com",
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

        # Now: 3 slots available (6 max - 1 organizer - 2 bookings)
        available = EventService.get_available_slots(event)
        self.assertEqual(available, MAX_PARTICIPANTS_PER_EVENT - 3)


    def test_validate_draft_limit_success(self):
        """Test A2: Should allow creating draft when under limit (< 3)."""
        # Create 2 drafts
        for i in range(2):
            Event.objects.create(
                organizer=self.user,
                partner=self.partner,
                language=self.language,
                theme=f"Draft {i}",
                difficulty="easy",
                datetime_start=timezone.now() + timedelta(days=i+1, hours=14),
                status=Event.Status.DRAFT,
            )

        # Should NOT raise exception
        EventService.validate_draft_limit(self.user)

    def test_validate_draft_limit_exceeded(self):
        """Test A2: Should reject 4th draft."""
        from rest_framework.exceptions import ValidationError

        for i in range(3):
            Event.objects.create(
                organizer=self.user,
                partner=self.partner,
                language=self.language,
                theme=f"Draft {i}",
                difficulty="easy",
                datetime_start=timezone.now() + timedelta(days=i+1, hours=14),
                status=Event.Status.DRAFT,
            )

        with self.assertRaises(ValidationError):
            EventService.validate_draft_limit(self.user)

    def test_transition_to_published_success(self):
        """Test A3: PENDING_CONFIRMATION ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¾ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ PUBLISHED."""
        # Create event in PENDING status
        event = Event.objects.create(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="Test Event",
            difficulty="easy",
            datetime_start=timezone.now() + timedelta(hours=4),
            status=Event.Status.PENDING_CONFIRMATION,
        )

        # Should succeed
        EventService.transition_to_published(event, published_by=self.user)

        event.refresh_from_db()
        self.assertEqual(event.status, Event.Status.PUBLISHED)
        self.assertIsNotNone(event.published_at)
        self.assertIsNotNone(event.organizer_paid_at)

    def test_transition_to_cancelled_published_with_3h_notice(self):
        """Test A3: PUBLISHED event can be cancelled with ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â°ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€¦Ã‚Â¡ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¥3h notice."""
        # Create event in 4 hours (enough time)
        event = Event.objects.create(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="Test Event",
            difficulty="easy",
            datetime_start=timezone.now() + timedelta(hours=4),
            status=Event.Status.PUBLISHED,
        )

        # Should succeed
        EventService.transition_to_cancelled(event, cancelled_by=self.user)

        event.refresh_from_db()
        self.assertEqual(event.status, Event.Status.CANCELLED)
        self.assertIsNotNone(event.cancelled_at)

