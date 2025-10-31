"""
Integration test: Complete booking flow.

Tests end-to-end flow from user registration to confirmed booking.
"""

from datetime import timedelta
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from languages.models import Language
from partners.models import Partner
from events.models import Event
from events.services import EventService
from bookings.models import Booking, BookingStatus
from bookings.services import BookingService
from payments.models import Payment
from payments.services import PaymentService
from payments.constants import STATUS_PENDING, STATUS_SUCCEEDED
from users.services import UserService

User = get_user_model()


class CompleteBookingFlowTest(TestCase):
    """
    Test complete end-to-end booking flow:
    1. User registration
    2. Organizer creates event (DRAFT)
    3. Organizer creates booking for their event
    4. Organizer pays → Event becomes PUBLISHED
    5. Participant registers
    6. Participant creates booking
    7. Participant pays → Booking CONFIRMED
    """

    def setUp(self):
        """Create base fixtures."""
        self.french = Language.objects.create(
            code="fr",
            label_fr="Français",
            label_en="French",
            label_nl="Frans",
            is_active=True,
        )
        self.english = Language.objects.create(
            code="en",
            label_fr="Anglais",
            label_en="English",
            label_nl="Engels",
            is_active=True,
        )
        self.partner = Partner.objects.create(
            name="Test Bar",
            address="123 Test St",
            city="Brussels",
            capacity=50,
            is_active=True,
        )

    def test_complete_booking_flow_paid_event(self):
        """
        Complete flow: Register → Create Event → Organizer Pays → Participant Books → Participant Pays
        """
        # ==============================================
        # STEP 1: Organizer registration
        # ==============================================
        organizer = UserService.create_user(
            email="organizer@example.com",
            password="securepass123",
            first_name="Alice",
            last_name="Organizer",
            age=30,
            native_langs=[self.french],
            target_langs=[self.english],
            consent_given=True,
        )
        self.assertIsNotNone(organizer)
        self.assertEqual(organizer.email, "organizer@example.com")

        # ==============================================
        # STEP 2: Organizer creates event
        # ==============================================
        datetime_start = timezone.now() + timedelta(days=3)
        datetime_start = datetime_start.replace(hour=18, minute=0, second=0, microsecond=0)

        event_data = {
            "partner": self.partner,
            "language": self.french,
            "theme": "Conversation française",
            "difficulty": "easy",  # Max 10 chars
            "datetime_start": datetime_start,
        }

        event, organizer_booking = EventService.create_event_with_organizer_booking(
            organizer=organizer,
            event_data=event_data
        )

        # Event should be DRAFT (awaiting organizer payment)
        self.assertEqual(event.status, "DRAFT")
        self.assertEqual(event.organizer, organizer)

        # Organizer booking should be PENDING
        self.assertEqual(organizer_booking.status, BookingStatus.PENDING)
        self.assertEqual(organizer_booking.user, organizer)
        self.assertEqual(organizer_booking.event, event)

        # ==============================================
        # STEP 3: Organizer pays (free event for test)
        # ==============================================
        # Simulate zero-amount payment (free event)
        event.price_cents = 0
        event.save()
        organizer_booking.amount_cents = 0
        organizer_booking.save()

        with patch('audit.services.AuditService.log_payment_succeeded'):
            stripe_url, session_id, payment = PaymentService.create_checkout_session(
                booking=organizer_booking,
                user=organizer,
                success_url="http://example.com/success",
                cancel_url="http://example.com/cancel",
            )

        # Zero-amount should skip Stripe (returns success_url, no session_id)
        self.assertEqual(stripe_url, "http://example.com/success")
        self.assertIsNone(session_id)

        # Booking should be CONFIRMED
        organizer_booking.refresh_from_db()
        self.assertEqual(organizer_booking.status, BookingStatus.CONFIRMED)

        # Event should be PUBLISHED (organizer paid)
        event.refresh_from_db()
        self.assertEqual(event.status, "PUBLISHED")

        # ==============================================
        # STEP 4: Participant registration
        # ==============================================
        participant = UserService.create_user(
            email="participant@example.com",
            password="securepass456",
            first_name="Bob",
            last_name="Participant",
            age=25,
            native_langs=[self.english],
            target_langs=[self.french],
            consent_given=True,
        )
        self.assertIsNotNone(participant)

        # ==============================================
        # STEP 5: Participant creates booking
        # ==============================================
        participant_booking = BookingService.create_booking(
            user=participant,
            event=event,
            amount_cents=700,  # Paid booking
        )

        self.assertEqual(participant_booking.status, BookingStatus.PENDING)
        self.assertEqual(participant_booking.amount_cents, 700)

        # ==============================================
        # STEP 6: Participant pays (mock Stripe)
        # ==============================================
        with patch('payments.services.payment_service.stripe.checkout.Session.create') as mock_stripe:
            with patch('audit.services.AuditService.log_payment_created'):
                # Mock Stripe session
                mock_session = MagicMock()
                mock_session.url = "https://checkout.stripe.com/session123"
                mock_session.id = "cs_test_123"
                mock_stripe.return_value = mock_session

                stripe_url, session_id, payment = PaymentService.create_checkout_session(
                    booking=participant_booking,
                    user=participant,
                    success_url="http://example.com/success",
                    cancel_url="http://example.com/cancel",
                )

        # Should have Stripe URL
        self.assertEqual(stripe_url, "https://checkout.stripe.com/session123")
        self.assertEqual(session_id, "cs_test_123")

        # Payment should be PENDING
        self.assertEqual(payment.status, STATUS_PENDING)

        # ==============================================
        # STEP 7: Simulate Stripe webhook (payment success)
        # ==============================================
        with patch('audit.services.AuditService.log_payment_succeeded'):
            PaymentService.confirm_payment_from_webhook(
                booking_public_id=str(participant_booking.public_id),
                session_id=session_id,
                payment_intent_id="pi_test_456",
                raw_event={"type": "checkout.session.completed"},
            )

        # Booking should be CONFIRMED
        participant_booking.refresh_from_db()
        self.assertEqual(participant_booking.status, BookingStatus.CONFIRMED)

        # Payment should be SUCCEEDED
        payment.refresh_from_db()
        self.assertEqual(payment.status, STATUS_SUCCEEDED)

        # ==============================================
        # VERIFICATION: Final state
        # ==============================================
        # Event should have 2 confirmed bookings
        confirmed_bookings = event.bookings.filter(status=BookingStatus.CONFIRMED).count()
        self.assertEqual(confirmed_bookings, 2)  # Organizer + Participant

        # Event should still be PUBLISHED
        event.refresh_from_db()
        self.assertEqual(event.status, "PUBLISHED")

        # Both users should have confirmed bookings
        self.assertTrue(
            Booking.objects.filter(user=organizer, event=event, status=BookingStatus.CONFIRMED).exists()
        )
        self.assertTrue(
            Booking.objects.filter(user=participant, event=event, status=BookingStatus.CONFIRMED).exists()
        )


class MultipleParticipantsBookingFlowTest(TestCase):
    """
    Test flow with multiple participants booking same event.
    """

    def setUp(self):
        """Create fixtures."""
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
            capacity=10,  # Small capacity
            is_active=True,
        )

        # Create organizer and published event
        self.organizer = User.objects.create_user(
            email="organizer@example.com",
            password="pass",
            age=30,
            consent_given=True,
        )

        datetime_start = timezone.now() + timedelta(days=2)
        datetime_start = datetime_start.replace(hour=18, minute=0, second=0, microsecond=0)

        self.event = Event.objects.create(
            organizer=self.organizer,
            partner=self.partner,
            language=self.language,
            theme="Test Event",
            difficulty="easy",
            datetime_start=datetime_start,
            status="PUBLISHED",
            price_cents=0,  # Free
        )

    def test_multiple_participants_can_book_same_event(self):
        """Multiple users should be able to book the same event until capacity reached."""
        # Create 5 participants
        participants = []
        for i in range(5):
            user = User.objects.create_user(
                email=f"user{i}@example.com",
                password="pass",
                age=25,
                consent_given=True,
            )
            participants.append(user)

        # All 5 participants book the event
        bookings = []
        for user in participants:
            booking = BookingService.create_booking(
                user=user,
                event=self.event,
                amount_cents=0,
            )
            bookings.append(booking)

        # Confirm all bookings
        for booking in bookings:
            booking.mark_confirmed()

        # Verify all bookings are CONFIRMED
        self.assertEqual(
            Booking.objects.filter(event=self.event, status=BookingStatus.CONFIRMED).count(),
            5
        )

        # Verify available capacity decreased
        available = self.event.available_slots
        self.assertEqual(available, 5)  # 10 total - 5 confirmed = 5 available


class ConcurrentBookingRaceConditionTest(TestCase):
    """
    Test edge case: Two users try to book last available spot simultaneously.
    """

    def setUp(self):
        """Create fixtures."""
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
            capacity=4,  # Very small capacity (min=3, only 1 extra slot)
            is_active=True,
        )

        organizer = User.objects.create_user(
            email="organizer@example.com",
            password="pass",
            age=30,
            consent_given=True,
        )

        datetime_start = timezone.now() + timedelta(days=2)
        datetime_start = datetime_start.replace(hour=18, minute=0, second=0, microsecond=0)

        self.event = Event.objects.create(
            organizer=organizer,
            partner=self.partner,
            language=self.language,
            theme="Small Event",
            difficulty="easy",
            datetime_start=datetime_start,
            status="PUBLISHED",
        )

    def test_booking_validates_capacity_at_creation(self):
        """Booking creation should validate capacity and fail when event is full."""
        # Fill capacity completely (4/4 - partner capacity is 4)
        for i in range(4):
            user = User.objects.create_user(
                email=f"user{i}@example.com",
                password="pass",
                age=25,
                consent_given=True,
            )
            booking = Booking.objects.create(
                user=user,
                event=self.event,
                amount_cents=700,
                status=BookingStatus.CONFIRMED,
            )

        # Now 0 spots available (4 - 4 = 0)
        # Try to create new booking should fail (event full)
        new_user = User.objects.create_user(
            email="newuser@example.com",
            password="pass",
            age=25,
            consent_given=True,
        )

        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError) as cm:
            BookingService.create_booking(
                user=new_user,
                event=self.event,
            )

        self.assertIn("full", str(cm.exception).lower())
