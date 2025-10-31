"""
Tests for RefundService business logic.

Tests automatic refund processing for cancelled bookings.
"""

from datetime import timedelta
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from languages.models import Language
from partners.models import Partner
from events.models import Event
from bookings.models import Booking, BookingStatus
from payments.models import Payment
from payments.services import RefundService
from payments.constants import (
    STATUS_SUCCEEDED,
    REFUND_DEADLINE_HOURS,
)

User = get_user_model()


class RefundServiceTest(TestCase):
    """Test suite for RefundService."""

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

    @patch('payments.services.refund_service.stripe.Refund.create')
    @patch('payments.services.refund_service.AuditService.log_payment_refunded')
    def test_process_refund_success(self, mock_audit, mock_stripe_refund):
        """Should process Stripe refund and create refund payment record."""
        # Create event 4h in future (beyond 3h deadline)
        event = Event.objects.create(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="Test Event",
            difficulty="easy",
            datetime_start=timezone.now() + timedelta(hours=4),
            price_cents=700,
            status="PUBLISHED",
        )

        booking = Booking.objects.create(
            user=self.user,
            event=event,
            amount_cents=700,
            status=BookingStatus.CONFIRMED,
        )

        # Create successful payment
        payment = Payment.objects.create(
            user=self.user,
            booking=booking,
            amount_cents=700,
            status=STATUS_SUCCEEDED,
            stripe_payment_intent_id="pi_test_123",
        )

        # Mock Stripe refund
        mock_refund = MagicMock()
        mock_refund.id = "re_test_456"
        mock_refund.status = "succeeded"
        mock_stripe_refund.return_value = mock_refund

        # Process refund
        success, message, refund_payment = RefundService.process_refund(
            booking=booking,
            cancelled_by=self.user,
        )

        # Verify success
        self.assertTrue(success)
        self.assertIn("re_test_456", message)
        self.assertIsNotNone(refund_payment)

        # Verify refund payment record (negative amount)
        self.assertEqual(refund_payment.amount_cents, -700)
        self.assertEqual(refund_payment.status, STATUS_SUCCEEDED)
        self.assertEqual(refund_payment.booking, booking)

        # Verify Stripe called
        mock_stripe_refund.assert_called_once()
        call_kwargs = mock_stripe_refund.call_args[1]
        self.assertEqual(call_kwargs['payment_intent'], "pi_test_123")

        # Verify audit log
        mock_audit.assert_called_once()

    @patch('payments.services.refund_service.AuditService.log_payment_refunded')
    def test_process_refund_zero_amount(self, mock_audit):
        """Should handle zero-amount refund without Stripe."""
        event = Event.objects.create(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="Free Event",
            difficulty="easy",
            datetime_start=timezone.now() + timedelta(hours=4),
            price_cents=0,
            status="PUBLISHED",
        )

        booking = Booking.objects.create(
            user=self.user,
            event=event,
            amount_cents=0,
            status=BookingStatus.CONFIRMED,
        )

        # Create zero-amount payment
        payment = Payment.objects.create(
            user=self.user,
            booking=booking,
            amount_cents=0,
            status=STATUS_SUCCEEDED,
        )

        # Process refund
        success, message, refund_payment = RefundService.process_refund(
            booking=booking,
            cancelled_by=self.user,
        )

        # Verify success
        self.assertTrue(success)
        self.assertIn("Free booking", message)
        self.assertIsNotNone(refund_payment)

        # Verify refund payment record
        self.assertEqual(refund_payment.amount_cents, 0)
        self.assertEqual(refund_payment.status, STATUS_SUCCEEDED)

        # Verify audit log
        mock_audit.assert_called_once()

    def test_process_refund_booking_not_confirmed(self):
        """Should raise ValidationError for PENDING booking."""
        event = Event.objects.create(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="Test Event",
            difficulty="easy",
            datetime_start=timezone.now() + timedelta(hours=4),
            status="PUBLISHED",
        )

        booking = Booking.objects.create(
            user=self.user,
            event=event,
            amount_cents=700,
            status=BookingStatus.PENDING,
        )

        with self.assertRaises(ValidationError) as cm:
            RefundService.process_refund(booking=booking, cancelled_by=self.user)

        self.assertIn("CONFIRMED", str(cm.exception))

    def test_process_refund_booking_cancelled(self):
        """Should raise ValidationError for already CANCELLED booking."""
        event = Event.objects.create(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="Test Event",
            difficulty="easy",
            datetime_start=timezone.now() + timedelta(hours=4),
            status="PUBLISHED",
        )

        booking = Booking.objects.create(
            user=self.user,
            event=event,
            amount_cents=700,
            status=BookingStatus.CANCELLED,
        )

        with self.assertRaises(ValidationError) as cm:
            RefundService.process_refund(booking=booking, cancelled_by=self.user)

        self.assertIn("cancelled", str(cm.exception))

    def test_process_refund_deadline_passed(self):
        """Should raise ValidationError when within 3h of event."""
        # Event only 2h away (within 3h deadline)
        event = Event.objects.create(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="Test Event",
            difficulty="easy",
            datetime_start=timezone.now() + timedelta(hours=2),
            status="PUBLISHED",
        )

        booking = Booking.objects.create(
            user=self.user,
            event=event,
            amount_cents=700,
            status=BookingStatus.CONFIRMED,
        )

        Payment.objects.create(
            user=self.user,
            booking=booking,
            amount_cents=700,
            status=STATUS_SUCCEEDED,
            stripe_payment_intent_id="pi_test_123",
        )

        with self.assertRaises(ValidationError) as cm:
            RefundService.process_refund(booking=booking, cancelled_by=self.user)

        self.assertIn(f"{REFUND_DEADLINE_HOURS}h", str(cm.exception))

    def test_process_refund_event_already_started(self):
        """Should raise ValidationError for event that started."""
        # Event started 1h ago
        event = Event.objects.create(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="Test Event",
            difficulty="easy",
            datetime_start=timezone.now() - timedelta(hours=1),
            status="PUBLISHED",
        )

        booking = Booking.objects.create(
            user=self.user,
            event=event,
            amount_cents=700,
            status=BookingStatus.CONFIRMED,
        )

        Payment.objects.create(
            user=self.user,
            booking=booking,
            amount_cents=700,
            status=STATUS_SUCCEEDED,
            stripe_payment_intent_id="pi_test_123",
        )

        with self.assertRaises(ValidationError) as cm:
            RefundService.process_refund(booking=booking, cancelled_by=self.user)

        self.assertIn("already started", str(cm.exception))

    def test_process_refund_no_payment_found(self):
        """Should return False when no successful payment exists."""
        event = Event.objects.create(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="Test Event",
            difficulty="easy",
            datetime_start=timezone.now() + timedelta(hours=4),
            status="PUBLISHED",
        )

        booking = Booking.objects.create(
            user=self.user,
            event=event,
            amount_cents=700,
            status=BookingStatus.CONFIRMED,
        )

        # No payment created

        success, message, payment = RefundService.process_refund(
            booking=booking,
            cancelled_by=self.user,
        )

        self.assertFalse(success)
        self.assertIn("No successful payment", message)
        self.assertIsNone(payment)

    def test_process_refund_payment_already_refunded(self):
        """Should return False when payment already refunded (negative amount)."""
        event = Event.objects.create(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="Test Event",
            difficulty="easy",
            datetime_start=timezone.now() + timedelta(hours=4),
            status="PUBLISHED",
        )

        booking = Booking.objects.create(
            user=self.user,
            event=event,
            amount_cents=700,
            status=BookingStatus.CONFIRMED,
        )

        # Create refund payment (negative amount)
        payment = Payment.objects.create(
            user=self.user,
            booking=booking,
            amount_cents=-700,  # Already refunded
            status=STATUS_SUCCEEDED,
        )

        success, message, refund_payment = RefundService.process_refund(
            booking=booking,
            cancelled_by=self.user,
        )

        self.assertFalse(success)
        self.assertIn("already refunded", message)

    @patch('payments.services.refund_service.stripe.Refund.create')
    def test_process_refund_stripe_failure(self, mock_stripe_refund):
        """Should raise error when Stripe refund fails."""
        event = Event.objects.create(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="Test Event",
            difficulty="easy",
            datetime_start=timezone.now() + timedelta(hours=4),
            status="PUBLISHED",
        )

        booking = Booking.objects.create(
            user=self.user,
            event=event,
            amount_cents=700,
            status=BookingStatus.CONFIRMED,
        )

        Payment.objects.create(
            user=self.user,
            booking=booking,
            amount_cents=700,
            status=STATUS_SUCCEEDED,
            stripe_payment_intent_id="pi_test_123",
        )

        # Mock Stripe failure
        import stripe
        mock_stripe_refund.side_effect = stripe.error.InvalidRequestError(
            "Charge already refunded", None
        )

        with self.assertRaises(stripe.error.InvalidRequestError):
            RefundService.process_refund(booking=booking, cancelled_by=self.user)

    @patch('payments.services.refund_service.stripe.Refund.create')
    @patch('payments.services.refund_service.AuditService.log_payment_refunded')
    def test_process_refund_no_payment_intent(self, mock_audit, mock_stripe_refund):
        """Should return False when payment has no payment_intent_id."""
        event = Event.objects.create(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="Test Event",
            difficulty="easy",
            datetime_start=timezone.now() + timedelta(hours=4),
            status="PUBLISHED",
        )

        booking = Booking.objects.create(
            user=self.user,
            event=event,
            amount_cents=700,
            status=BookingStatus.CONFIRMED,
        )

        # Payment without payment_intent_id
        Payment.objects.create(
            user=self.user,
            booking=booking,
            amount_cents=700,
            status=STATUS_SUCCEEDED,
            stripe_payment_intent_id=None,  # Missing
        )

        success, message, payment = RefundService.process_refund(
            booking=booking,
            cancelled_by=self.user,
        )

        self.assertFalse(success)
        self.assertIn("No payment intent", message)
        self.assertIsNone(payment)

    @patch('payments.services.refund_service.stripe.Refund.create')
    @patch('payments.services.refund_service.AuditService.log_payment_refunded')
    def test_process_refund_uses_latest_payment(self, mock_audit, mock_stripe_refund):
        """Should refund the most recent successful payment."""
        event = Event.objects.create(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="Test Event",
            difficulty="easy",
            datetime_start=timezone.now() + timedelta(hours=4),
            status="PUBLISHED",
        )

        booking = Booking.objects.create(
            user=self.user,
            event=event,
            amount_cents=700,
            status=BookingStatus.CONFIRMED,
        )

        # Create multiple payments (older)
        Payment.objects.create(
            user=self.user,
            booking=booking,
            amount_cents=700,
            status=STATUS_SUCCEEDED,
            stripe_payment_intent_id="pi_old_123",
            created_at=timezone.now() - timedelta(hours=1),
        )

        # Latest payment
        latest_payment = Payment.objects.create(
            user=self.user,
            booking=booking,
            amount_cents=700,
            status=STATUS_SUCCEEDED,
            stripe_payment_intent_id="pi_latest_456",
        )

        # Mock Stripe refund
        mock_refund = MagicMock()
        mock_refund.id = "re_test_789"
        mock_stripe_refund.return_value = mock_refund

        # Process refund
        RefundService.process_refund(booking=booking, cancelled_by=self.user)

        # Verify latest payment was refunded
        call_kwargs = mock_stripe_refund.call_args[1]
        self.assertEqual(call_kwargs['payment_intent'], "pi_latest_456")
