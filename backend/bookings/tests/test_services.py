"""
Tests for BookingService business logic.

These tests ensure booking creation, cancellation, and expiration
work correctly.
"""

from datetime import timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from languages.models import Language
from partners.models import Partner
from events.models import Event
from bookings.models import Booking, BookingStatus
from bookings.services import BookingService
from common.exceptions import EventFullError, CancellationDeadlineError

User = get_user_model()


class BookingServiceTestCase(TestCase):
    """Test suite for BookingService."""

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
        self.event = Event.objects.create(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="Test Event",
            difficulty="easy",
            datetime_start=timezone.now() + timedelta(days=2),
            status="PUBLISHED",  # Event must be PUBLISHED for capacity calculations
        )

    def test_create_booking(self):
        """Should create booking with correct defaults."""
        booking = BookingService.create_booking(
            user=self.user,
            event=self.event,
        )

        self.assertEqual(booking.user, self.user)
        self.assertEqual(booking.event, self.event)
        self.assertEqual(booking.status, BookingStatus.PENDING)
        self.assertEqual(booking.amount_cents, self.event.price_cents)
        self.assertIsNotNone(booking.expires_at)

    def test_create_booking_fails_when_event_full(self):
        """Should raise error when partner has insufficient capacity (< 3 available)."""
        # Fill partner capacity to 48/50 (leaving only 2 available, < 3 minimum)
        for i in range(48):
            user = User.objects.create_user(
                email=f"user{i}@example.com",
                password="pass",
                age=20,
                consent_given=True,
            )
            Booking.objects.create(
                user=user,
                event=self.event,
                amount_cents=700,
                status=BookingStatus.CONFIRMED,
            )

        # Try to create one more booking (only 2 available, need 3 minimum)
        new_user = User.objects.create_user(
            email="extra@example.com",
            password="pass",
            age=20,
            consent_given=True,
        )

        with self.assertRaises(Exception):  # Should raise validation error
            BookingService.create_booking(
                user=new_user,
                event=self.event,
            )

    def test_auto_expire_bookings(self):
        """Should auto-expire PENDING bookings past expiration."""
        # Create expired booking
        booking = Booking.objects.create(
            user=self.user,
            event=self.event,
            amount_cents=700,
            status=BookingStatus.PENDING,
            expires_at=timezone.now() - timedelta(minutes=1),  # Already expired
        )

        # Run auto-expiration
        count = BookingService.auto_expire_bookings()

        self.assertEqual(count, 1)

        booking.refresh_from_db()
        self.assertEqual(booking.status, BookingStatus.CANCELLED)

    def test_confirm_booking(self):
        """Should confirm booking after payment."""
        booking = Booking.objects.create(
            user=self.user,
            event=self.event,
            amount_cents=700,
            status=BookingStatus.PENDING,
        )

        BookingService.confirm_booking(
            booking=booking,
            payment_intent_id="pi_test123",
        )

        booking.refresh_from_db()
        self.assertEqual(booking.status, BookingStatus.CONFIRMED)
        self.assertEqual(booking.payment_intent_id, "pi_test123")
        self.assertIsNotNone(booking.confirmed_at)

    def test_can_cancel_booking_respects_deadline(self):
        """Should prevent cancellation within 3h of event."""
        # Create event starting in 2 hours (within 3h deadline)
        near_event = Event.objects.create(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="Near Event",
            difficulty="easy",
            datetime_start=timezone.now() + timedelta(hours=2),
        )

        booking = Booking.objects.create(
            user=self.user,
            event=near_event,
            amount_cents=700,
            status=BookingStatus.CONFIRMED,
        )

        can_cancel, reason = BookingService.can_cancel_booking(booking)

        self.assertFalse(can_cancel)
        self.assertIn("3h", reason)

    def test_get_user_bookings(self):
        """Should retrieve user's bookings with filters."""
        # Create multiple bookings
        Booking.objects.create(
            user=self.user,
            event=self.event,
            amount_cents=700,
            status=BookingStatus.PENDING,
        )
        Booking.objects.create(
            user=self.user,
            event=self.event,
            amount_cents=700,
            status=BookingStatus.CONFIRMED,
        )

        # Get all bookings
        all_bookings = BookingService.get_user_bookings(self.user)
        self.assertEqual(all_bookings.count(), 2)

        # Filter by status
        confirmed = BookingService.get_user_bookings(
            self.user,
            status=BookingStatus.CONFIRMED,
        )
        self.assertEqual(confirmed.count(), 1)
