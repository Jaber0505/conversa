"""
Edge case tests for Payments module.

Tests boundary conditions and validation rules.
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
from payments.services import PaymentService, RefundService
from payments.validators import (
    validate_payment_retry_limit,
    validate_refund_eligibility,
)
from payments.constants import (
    MAX_PAYMENT_RETRIES,
    STATUS_PENDING,
    STATUS_SUCCEEDED,
    REFUND_DEADLINE_HOURS,
)

User = get_user_model()


class PaymentRetryLimitEdgeCasesTest(TestCase):
    """Test edge cases for payment retry limit (max 3 attempts)."""

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
            price_cents=700,
            status="PUBLISHED",
        )
        self.booking = Booking.objects.create(
            user=self.user,
            event=self.event,
            amount_cents=700,
            status=BookingStatus.PENDING,
        )

    def test_payment_retry_with_2_attempts_should_pass(self):
        """Should allow 3rd payment attempt when only 2 exist."""
        # Create 2 payment attempts
        for i in range(2):
            Payment.objects.create(
                user=self.user,
                booking=self.booking,
                amount_cents=700,
                status=STATUS_PENDING,
            )

        # Validate retry limit (should not raise)
        validate_payment_retry_limit(self.booking)

    def test_payment_retry_with_3_attempts_should_fail(self):
        """Should block 4th payment attempt when 3 already exist (max reached)."""
        # Create 3 payment attempts (MAX_PAYMENT_RETRIES)
        for i in range(MAX_PAYMENT_RETRIES):
            Payment.objects.create(
                user=self.user,
                booking=self.booking,
                amount_cents=700,
                status=STATUS_PENDING,
            )

        # Validate retry limit (should raise)
        with self.assertRaises(ValidationError) as cm:
            validate_payment_retry_limit(self.booking)

        self.assertIn("retry limit exceeded", str(cm.exception))
        self.assertIn("3", str(cm.exception))

    @patch('payments.services.payment_service.stripe.checkout.Session.create')
    def test_create_checkout_session_4th_attempt_should_fail(self, mock_stripe):
        """4th checkout session attempt should fail."""
        # Create 3 payment attempts
        for i in range(MAX_PAYMENT_RETRIES):
            Payment.objects.create(
                user=self.user,
                booking=self.booking,
                amount_cents=700,
                status=STATUS_PENDING,
            )

        # Try to create 4th checkout session (should raise)
        with self.assertRaises(ValidationError) as cm:
            PaymentService.create_checkout_session(
                booking=self.booking,
                user=self.user,
                success_url="http://example.com/success",
                cancel_url="http://example.com/cancel",
            )

        self.assertIn("retry limit", str(cm.exception))

    def test_payment_retry_count_includes_all_statuses(self):
        """Retry limit counts ALL payment records regardless of status."""
        # Create 1 PENDING, 1 SUCCEEDED, 1 FAILED
        Payment.objects.create(
            user=self.user,
            booking=self.booking,
            amount_cents=700,
            status=STATUS_PENDING,
        )
        Payment.objects.create(
            user=self.user,
            booking=self.booking,
            amount_cents=700,
            status=STATUS_SUCCEEDED,
        )
        Payment.objects.create(
            user=self.user,
            booking=self.booking,
            amount_cents=700,
            status="failed",
        )

        # Total = 3, should block 4th attempt
        with self.assertRaises(ValidationError) as cm:
            validate_payment_retry_limit(self.booking)

        self.assertIn("retry limit exceeded", str(cm.exception))


class RefundDeadlineEdgeCasesTest(TestCase):
    """Test edge cases for refund deadline (3h before event)."""

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

    def test_refund_at_2h59_before_event_should_pass(self):
        """Refund at 2h59 before event should pass (before 3h deadline)."""
        event = Event.objects.create(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="Test Event",
            difficulty="easy",
            datetime_start=timezone.now() + timedelta(hours=2, minutes=59),
            status="PUBLISHED",
        )

        booking = Booking.objects.create(
            user=self.user,
            event=event,
            amount_cents=700,
            status=BookingStatus.CONFIRMED,
        )

        # Should not raise (before deadline)
        validate_refund_eligibility(booking)

    def test_refund_at_3h00_exactly_should_fail(self):
        """Refund at exactly 3h before event should fail (at deadline)."""
        event = Event.objects.create(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="Test Event",
            difficulty="easy",
            datetime_start=timezone.now() + timedelta(hours=3, minutes=0, seconds=0),
            status="PUBLISHED",
        )

        booking = Booking.objects.create(
            user=self.user,
            event=event,
            amount_cents=700,
            status=BookingStatus.CONFIRMED,
        )

        # Should raise (at deadline)
        with self.assertRaises(ValidationError) as cm:
            validate_refund_eligibility(booking)

        self.assertIn(f"{REFUND_DEADLINE_HOURS}h", str(cm.exception))

    def test_refund_at_3h01_before_event_should_pass(self):
        """Refund at 3h01 before event should pass (outside deadline)."""
        event = Event.objects.create(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="Test Event",
            difficulty="easy",
            datetime_start=timezone.now() + timedelta(hours=3, minutes=1),
            status="PUBLISHED",
        )

        booking = Booking.objects.create(
            user=self.user,
            event=event,
            amount_cents=700,
            status=BookingStatus.CONFIRMED,
        )

        # Should not raise (outside deadline)
        validate_refund_eligibility(booking)

    def test_refund_for_event_already_started_should_fail(self):
        """Refund for event that already started should fail."""
        event = Event.objects.create(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="Past Event",
            difficulty="easy",
            datetime_start=timezone.now() - timedelta(hours=1),  # Started 1h ago
            status="PUBLISHED",
        )

        booking = Booking.objects.create(
            user=self.user,
            event=event,
            amount_cents=700,
            status=BookingStatus.CONFIRMED,
        )

        with self.assertRaises(ValidationError) as cm:
            validate_refund_eligibility(booking)

        self.assertIn("already started", str(cm.exception))


class RefundEligibilityEdgeCasesTest(TestCase):
    """Test edge cases for refund eligibility by booking status."""

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
            datetime_start=timezone.now() + timedelta(hours=4),
            status="PUBLISHED",
        )

    def test_refund_pending_booking_should_fail(self):
        """PENDING booking should not be refundable (not paid yet)."""
        booking = Booking.objects.create(
            user=self.user,
            event=self.event,
            amount_cents=700,
            status=BookingStatus.PENDING,
        )

        with self.assertRaises(ValidationError) as cm:
            validate_refund_eligibility(booking)

        self.assertIn("CONFIRMED", str(cm.exception))

    def test_refund_cancelled_booking_should_fail(self):
        """CANCELLED booking should not be refundable."""
        booking = Booking.objects.create(
            user=self.user,
            event=self.event,
            amount_cents=700,
            status=BookingStatus.CANCELLED,
        )

        with self.assertRaises(ValidationError) as cm:
            validate_refund_eligibility(booking)

        self.assertIn("cancelled", str(cm.exception).lower())

    def test_refund_confirmed_booking_should_pass(self):
        """CONFIRMED booking should be refundable (if within deadline)."""
        booking = Booking.objects.create(
            user=self.user,
            event=self.event,
            amount_cents=700,
            status=BookingStatus.CONFIRMED,
        )

        # Should not raise
        validate_refund_eligibility(booking)


class PaymentZeroAmountEdgeCasesTest(TestCase):
    """Test edge cases for zero-amount (free) bookings."""

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
            theme="Free Event",
            difficulty="easy",
            datetime_start=timezone.now() + timedelta(days=2),
            price_cents=0,  # Free!
            status="PUBLISHED",
        )

    @patch('payments.services.payment_service.AuditService.log_payment_succeeded')
    def test_zero_amount_checkout_skips_stripe(self, mock_audit):
        """Zero-amount booking should skip Stripe and auto-confirm."""
        booking = Booking.objects.create(
            user=self.user,
            event=self.event,
            amount_cents=0,
            status=BookingStatus.PENDING,
        )

        stripe_url, session_id, payment = PaymentService.create_checkout_session(
            booking=booking,
            user=self.user,
            success_url="http://example.com/success",
            cancel_url="http://example.com/cancel",
        )

        # Should return None for Stripe data
        self.assertIsNone(stripe_url)
        self.assertIsNone(session_id)

        # Should create payment with SUCCESS status
        self.assertIsNotNone(payment)
        self.assertEqual(payment.amount_cents, 0)
        self.assertEqual(payment.status, STATUS_SUCCEEDED)

        # Should auto-confirm booking
        booking.refresh_from_db()
        self.assertEqual(booking.status, BookingStatus.CONFIRMED)

        # Should log with is_free=True
        mock_audit.assert_called_once()
        call_kwargs = mock_audit.call_args[1]
        self.assertTrue(call_kwargs.get('is_free'))

    @patch('payments.services.refund_service.AuditService.log_payment_refunded')
    def test_zero_amount_refund_skips_stripe(self, mock_audit):
        """Zero-amount refund should skip Stripe."""
        booking = Booking.objects.create(
            user=self.user,
            event=self.event,
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

        success, message, refund_payment = RefundService.process_refund(
            booking=booking,
            cancelled_by=self.user,
        )

        # Should succeed
        self.assertTrue(success)
        self.assertIn("Free booking", message)

        # Should create refund payment
        self.assertIsNotNone(refund_payment)
        self.assertEqual(refund_payment.amount_cents, 0)

        # Should log with is_free=True
        mock_audit.assert_called_once()
        call_kwargs = mock_audit.call_args[1]
        self.assertTrue(call_kwargs.get('is_free'))


class PaymentAlreadyRefundedEdgeCasesTest(TestCase):
    """Test edge cases for already refunded payments."""

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
            datetime_start=timezone.now() + timedelta(hours=4),
            status="PUBLISHED",
        )

    def test_refund_already_refunded_payment_should_fail(self):
        """Attempting to refund a payment that was already refunded should fail."""
        booking = Booking.objects.create(
            user=self.user,
            event=self.event,
            amount_cents=700,
            status=BookingStatus.CONFIRMED,
        )

        # Create original payment
        payment = Payment.objects.create(
            user=self.user,
            booking=booking,
            amount_cents=700,
            status=STATUS_SUCCEEDED,
            stripe_payment_intent_id="pi_test_123",
        )

        # Create refund payment (negative amount)
        refund_payment = Payment.objects.create(
            user=self.user,
            booking=booking,
            amount_cents=-700,  # Negative = refund
            status=STATUS_SUCCEEDED,
        )

        # Replace original payment with refund as latest
        payment.created_at = timezone.now() - timedelta(minutes=1)
        payment.save()

        # Try to refund again (should detect already refunded)
        success, message, result_payment = RefundService.process_refund(
            booking=booking,
            cancelled_by=self.user,
        )

        self.assertFalse(success)
        self.assertIn("already refunded", message.lower())
