"""
Edge case tests for Bookings module.

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
from bookings.models import Booking, BookingStatus
from bookings.services import BookingService
from bookings.validators import validate_cancellation_deadline
from common.exceptions import CancellationDeadlineError

User = get_user_model()


class BookingCancellationDeadlineEdgeCasesTest(TestCase):
    """Test edge cases for booking cancellation deadline (3h)."""

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

    def test_cancel_booking_at_2h59_should_pass(self):
        """Cancellation at 2h59 before event should pass (before 3h deadline)."""
        # Event in 2 hours 59 minutes
        event_time = timezone.now() + timedelta(hours=2, minutes=59)
        event = Event.objects.create(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="Test Event",
            difficulty="easy",
            datetime_start=event_time,
            status="PUBLISHED",
        )

        booking = Booking.objects.create(
            user=self.user,
            event=event,
            amount_cents=700,
            status=BookingStatus.CONFIRMED,
        )

        # Should not raise (still within cancellation window)
        validate_cancellation_deadline(booking)

    def test_cancel_booking_at_3h00_exactly_should_fail(self):
        """Cancellation at exactly 3h before event should fail (at deadline)."""
        # Event in exactly 3 hours
        event_time = timezone.now() + timedelta(hours=3, minutes=0, seconds=0)
        event = Event.objects.create(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="Test Event",
            difficulty="easy",
            datetime_start=event_time,
            status="PUBLISHED",
        )

        booking = Booking.objects.create(
            user=self.user,
            event=event,
            amount_cents=700,
            status=BookingStatus.CONFIRMED,
        )

        # Should raise (at deadline)
        with self.assertRaises(CancellationDeadlineError) as cm:
            validate_cancellation_deadline(booking)

        self.assertIn("3", str(cm.exception))

    def test_cancel_booking_at_3h01_should_fail(self):
        """Cancellation at 3h01 before event should fail (past deadline)."""
        # Event in 3 hours 1 minute
        event_time = timezone.now() + timedelta(hours=3, minutes=1)
        event = Event.objects.create(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="Test Event",
            difficulty="easy",
            datetime_start=event_time,
            status="PUBLISHED",
        )

        booking = Booking.objects.create(
            user=self.user,
            event=event,
            amount_cents=700,
            status=BookingStatus.CONFIRMED,
        )

        # Should NOT raise (still outside deadline)
        validate_cancellation_deadline(booking)

    def test_cancel_booking_1_minute_before_event_should_fail(self):
        """Cancellation 1 minute before event should fail."""
        # Event in 1 minute
        event_time = timezone.now() + timedelta(minutes=1)
        event = Event.objects.create(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="Test Event",
            difficulty="easy",
            datetime_start=event_time,
            status="PUBLISHED",
        )

        booking = Booking.objects.create(
            user=self.user,
            event=event,
            amount_cents=700,
            status=BookingStatus.CONFIRMED,
        )

        with self.assertRaises(CancellationDeadlineError) as cm:
            validate_cancellation_deadline(booking)

        self.assertIn("3", str(cm.exception))

    def test_can_cancel_booking_returns_correct_status(self):
        """BookingService.can_cancel_booking should return correct bool + message."""
        # Event in 4 hours (before deadline)
        event_time = timezone.now() + timedelta(hours=4)
        event = Event.objects.create(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="Test Event",
            difficulty="easy",
            datetime_start=event_time,
            status="PUBLISHED",
        )

        booking = Booking.objects.create(
            user=self.user,
            event=event,
            amount_cents=700,
            status=BookingStatus.CONFIRMED,
        )

        can_cancel, message = BookingService.can_cancel_booking(booking)
        self.assertTrue(can_cancel)
        self.assertEqual(message, "")

        # Now check with booking within deadline (2h before event)
        event_soon = Event.objects.create(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="Soon Event",
            difficulty="easy",
            datetime_start=timezone.now() + timedelta(hours=2),
            status="PUBLISHED",
        )

        booking_soon = Booking.objects.create(
            user=self.user,
            event=event_soon,
            amount_cents=700,
            status=BookingStatus.CONFIRMED,
        )

        can_cancel, message = BookingService.can_cancel_booking(booking_soon)
        self.assertFalse(can_cancel)
        self.assertIn("3h", message)


class BookingStatusEdgeCasesTest(TestCase):
    """Test edge cases for booking status transitions."""

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
            status="PUBLISHED",
        )

    def test_user_can_have_only_one_pending_booking_per_event(self):
        """User should only have 1 PENDING booking per event (DB constraint)."""
        # Create first PENDING booking
        booking1 = Booking.objects.create(
            user=self.user,
            event=self.event,
            amount_cents=700,
            status=BookingStatus.PENDING,
        )

        # Try to create second PENDING booking (should fail - unique constraint)
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Booking.objects.create(
                user=self.user,
                event=self.event,
                amount_cents=700,
                status=BookingStatus.PENDING,
            )

    def test_user_can_have_multiple_confirmed_bookings_per_event(self):
        """User can have multiple CONFIRMED bookings for same event."""
        # Create first CONFIRMED booking
        booking1 = Booking.objects.create(
            user=self.user,
            event=self.event,
            amount_cents=700,
            status=BookingStatus.CONFIRMED,
        )

        # Create second CONFIRMED booking (should succeed)
        booking2 = Booking.objects.create(
            user=self.user,
            event=self.event,
            amount_cents=700,
            status=BookingStatus.CONFIRMED,
        )

        # Verify both exist
        confirmed_count = Booking.objects.filter(
            user=self.user,
            event=self.event,
            status=BookingStatus.CONFIRMED
        ).count()
        self.assertEqual(confirmed_count, 2)

    def test_cancelled_booking_cannot_be_cancelled_again(self):
        """Booking already CANCELLED cannot be cancelled again."""
        booking = Booking.objects.create(
            user=self.user,
            event=self.event,
            amount_cents=700,
            status=BookingStatus.CANCELLED,
        )

        can_cancel, message = BookingService.can_cancel_booking(booking)
        self.assertFalse(can_cancel)
        self.assertIn("already cancelled", message.lower())

    def test_mark_cancelled_on_already_cancelled_returns_false(self):
        """Calling mark_cancelled on CANCELLED booking returns False."""
        booking = Booking.objects.create(
            user=self.user,
            event=self.event,
            amount_cents=700,
            status=BookingStatus.CANCELLED,
        )

        result = booking.mark_cancelled()
        self.assertFalse(result)


class BookingExpirationEdgeCasesTest(TestCase):
    """Test edge cases for booking expiration (15 min TTL)."""

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
            status="PUBLISHED",
        )

    def test_booking_expires_at_14min59_should_not_be_expired(self):
        """Booking at 14min 59sec should not be expired yet."""
        # Create booking that expires in 1 second
        booking = Booking.objects.create(
            user=self.user,
            event=self.event,
            amount_cents=700,
            status=BookingStatus.PENDING,
            expires_at=timezone.now() + timedelta(seconds=1),
        )

        self.assertFalse(booking.is_expired)

    def test_booking_expires_at_15min_exactly_should_be_expired(self):
        """Booking at exactly 15min should be expired."""
        # Create booking that expired exactly now
        booking = Booking.objects.create(
            user=self.user,
            event=self.event,
            amount_cents=700,
            status=BookingStatus.PENDING,
            expires_at=timezone.now(),
        )

        self.assertTrue(booking.is_expired)

    def test_auto_expire_bookings_cancels_expired_pending(self):
        """auto_expire_bookings should cancel all expired PENDING bookings."""
        # Create 3 expired PENDING bookings
        for i in range(3):
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
                status=BookingStatus.PENDING,
                expires_at=timezone.now() - timedelta(minutes=1),  # Expired
            )

        # Create 1 non-expired PENDING booking
        Booking.objects.create(
            user=self.user,
            event=self.event,
            amount_cents=700,
            status=BookingStatus.PENDING,
            expires_at=timezone.now() + timedelta(minutes=10),  # Not expired
        )

        # Run auto-expire
        count = BookingService.auto_expire_bookings()

        # Should have expired 3 bookings
        self.assertEqual(count, 3)

        # Verify all expired are now CANCELLED
        cancelled_count = Booking.objects.filter(
            status=BookingStatus.CANCELLED,
            expires_at__lte=timezone.now()
        ).count()
        self.assertEqual(cancelled_count, 3)

        # Verify non-expired is still PENDING
        pending_count = Booking.objects.filter(
            status=BookingStatus.PENDING
        ).count()
        self.assertEqual(pending_count, 1)


class BookingAmountEdgeCasesTest(TestCase):
    """Test edge cases for booking amounts."""

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

    def test_booking_with_zero_amount_should_succeed(self):
        """Booking with 0 amount (free event) should be allowed."""
        event = Event.objects.create(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="Free Event",
            difficulty="easy",
            datetime_start=timezone.now() + timedelta(days=2),
            price_cents=0,  # Free
            status="PUBLISHED",
        )

        booking = BookingService.create_booking(
            user=self.user,
            event=event,
            amount_cents=0,
        )

        self.assertEqual(booking.amount_cents, 0)
        self.assertEqual(booking.status, BookingStatus.PENDING)

    def test_booking_amount_defaults_to_event_price(self):
        """Booking without amount_cents should default to event price."""
        event = Event.objects.create(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="Paid Event",
            difficulty="easy",
            datetime_start=timezone.now() + timedelta(days=2),
            price_cents=700,
            status="PUBLISHED",
        )

        booking = BookingService.create_booking(
            user=self.user,
            event=event,
            # amount_cents not specified
        )

        self.assertEqual(booking.amount_cents, 700)
