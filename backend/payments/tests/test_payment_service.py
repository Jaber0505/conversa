"""
Tests for PaymentService business logic.

Tests payment session creation, confirmation, and webhook handling.
"""

from datetime import timedelta
from unittest.mock import patch, MagicMock, Mock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from languages.models import Language
from partners.models import Partner
from events.models import Event
from bookings.models import Booking, BookingStatus
from payments.models import Payment
from payments.services import PaymentService
from payments.constants import (
    STATUS_PENDING,
    STATUS_SUCCEEDED,
    STATUS_FAILED,
    MAX_PAYMENT_RETRIES,
)

User = get_user_model()


class PaymentServiceTest(TestCase):
    """Test suite for PaymentService."""

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

    @patch('payments.services.payment_service.stripe.checkout.Session.create')
    @patch('payments.services.payment_service.AuditService.log_payment_created')
    def test_create_checkout_session_success(self, mock_audit, mock_stripe_create):
        """Should create Stripe session and Payment record."""
        # Mock Stripe response
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/session123"
        mock_session.id = "cs_test_123"
        mock_stripe_create.return_value = mock_session

        # Create checkout session
        stripe_url, session_id, payment = PaymentService.create_checkout_session(
            booking=self.booking,
            user=self.user,
            success_url="http://example.com/success",
            cancel_url="http://example.com/cancel",
        )

        # Verify results
        self.assertEqual(stripe_url, "https://checkout.stripe.com/session123")
        self.assertEqual(session_id, "cs_test_123")
        self.assertIsNotNone(payment)
        self.assertEqual(payment.booking, self.booking)
        self.assertEqual(payment.amount_cents, 700)
        self.assertEqual(payment.status, STATUS_PENDING)

        # Verify Stripe was called
        mock_stripe_create.assert_called_once()
        call_kwargs = mock_stripe_create.call_args[1]
        self.assertEqual(call_kwargs['line_items'][0]['price_data']['unit_amount'], 700)

        # Verify audit log
        mock_audit.assert_called_once_with(payment, self.user)

    @patch('payments.services.payment_service.AuditService.log_payment_succeeded')
    def test_create_checkout_session_zero_amount(self, mock_audit):
        """Should handle zero-amount booking without Stripe."""
        self.booking.amount_cents = 0
        self.booking.save()

        stripe_url, session_id, payment = PaymentService.create_checkout_session(
            booking=self.booking,
            user=self.user,
            success_url="http://example.com/success",
            cancel_url="http://example.com/cancel",
        )

        # Should return None for Stripe data
        self.assertIsNone(stripe_url)
        self.assertIsNone(session_id)

        # Should create payment and confirm booking
        self.assertIsNotNone(payment)
        self.assertEqual(payment.amount_cents, 0)
        self.assertEqual(payment.status, STATUS_SUCCEEDED)

        # Verify booking confirmed
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, BookingStatus.CONFIRMED)

        # Verify audit log
        mock_audit.assert_called_once()

    def test_create_checkout_session_booking_not_payable(self):
        """Should raise ValidationError for non-PENDING booking."""
        self.booking.status = BookingStatus.CONFIRMED
        self.booking.save()

        with self.assertRaises(ValidationError) as cm:
            PaymentService.create_checkout_session(
                booking=self.booking,
                user=self.user,
                success_url="http://example.com/success",
                cancel_url="http://example.com/cancel",
            )

        self.assertIn("not payable", str(cm.exception))

    def test_create_checkout_session_retry_limit_exceeded(self):
        """Should raise ValidationError when retry limit reached."""
        # Create max payment attempts
        for i in range(MAX_PAYMENT_RETRIES):
            Payment.objects.create(
                user=self.user,
                booking=self.booking,
                amount_cents=700,
                status=STATUS_PENDING,
            )

        with self.assertRaises(ValidationError) as cm:
            PaymentService.create_checkout_session(
                booking=self.booking,
                user=self.user,
                success_url="http://example.com/success",
                cancel_url="http://example.com/cancel",
            )

        self.assertIn("retry limit", str(cm.exception))

    @patch('payments.services.payment_service.AuditService.log_payment_succeeded')
    def test_confirm_payment_from_webhook(self, mock_audit):
        """Should confirm booking and update payment status."""
        # Create pending payment
        payment = Payment.objects.create(
            user=self.user,
            booking=self.booking,
            amount_cents=700,
            status=STATUS_PENDING,
            stripe_session_id="cs_test_123",
        )

        # Confirm payment via webhook
        PaymentService.confirm_payment_from_webhook(
            booking_public_id=str(self.booking.public_id),
            session_id="cs_test_123",
            payment_intent_id="pi_test_456",
            raw_event={"type": "checkout.session.completed"},
        )

        # Verify booking confirmed
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, BookingStatus.CONFIRMED)
        self.assertIsNotNone(self.booking.confirmed_at)

        # Verify payment updated
        payment.refresh_from_db()
        self.assertEqual(payment.status, STATUS_SUCCEEDED)
        self.assertEqual(payment.stripe_payment_intent_id, "pi_test_456")

        # Verify audit log
        mock_audit.assert_called_once_with(payment, self.user, is_free=False)

    def test_confirm_payment_webhook_booking_not_found(self):
        """Should raise ValidationError when booking doesn't exist."""
        with self.assertRaises(ValidationError) as cm:
            PaymentService.confirm_payment_from_webhook(
                booking_public_id="00000000-0000-0000-0000-000000000000",
                session_id="cs_test_123",
                payment_intent_id="pi_test_456",
                raw_event={},
            )

        self.assertIn("Booking not found", str(cm.exception))

    def test_confirm_payment_webhook_payment_not_found(self):
        """Should raise ValidationError when payment doesn't exist."""
        with self.assertRaises(ValidationError) as cm:
            PaymentService.confirm_payment_from_webhook(
                booking_public_id=str(self.booking.public_id),
                session_id="cs_nonexistent_123",
                payment_intent_id="pi_test_456",
                raw_event={},
            )

        self.assertIn("Payment not found", str(cm.exception))

    @patch('payments.services.payment_service.AuditService.log_payment_failed')
    def test_mark_payment_failed(self, mock_audit):
        """Should mark payment as failed and log event."""
        # Create pending payment
        payment = Payment.objects.create(
            user=self.user,
            booking=self.booking,
            amount_cents=700,
            status=STATUS_PENDING,
            stripe_session_id="cs_test_123",
        )

        # Mark as failed
        PaymentService.mark_payment_failed(
            session_id="cs_test_123",
            reason="Insufficient funds",
            raw_event={"type": "payment_intent.payment_failed"},
        )

        # Verify payment status
        payment.refresh_from_db()
        self.assertEqual(payment.status, STATUS_FAILED)

        # Verify audit log
        mock_audit.assert_called_once()

    def test_mark_payment_failed_payment_not_found(self):
        """Should not raise when payment doesn't exist (webhook may arrive late)."""
        # Should not raise
        PaymentService.mark_payment_failed(
            session_id="cs_nonexistent_123",
            reason="Test",
            raw_event={},
        )

    @patch('payments.services.payment_service.stripe.checkout.Session.create')
    def test_create_checkout_session_idempotent(self, mock_stripe_create):
        """Should reuse existing payment for same session."""
        # Mock Stripe response
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/session123"
        mock_session.id = "cs_test_123"
        mock_stripe_create.return_value = mock_session

        # Create first session
        url1, sid1, payment1 = PaymentService.create_checkout_session(
            booking=self.booking,
            user=self.user,
            success_url="http://example.com/success",
            cancel_url="http://example.com/cancel",
        )

        # Create second session (should update existing payment)
        mock_session.id = "cs_test_456"
        url2, sid2, payment2 = PaymentService.create_checkout_session(
            booking=self.booking,
            user=self.user,
            success_url="http://example.com/success",
            cancel_url="http://example.com/cancel",
        )

        # Should update same payment record
        self.assertEqual(payment1.id, payment2.id)
        self.assertEqual(payment2.stripe_session_id, "cs_test_456")

        # Should have only 2 payments (not 3)
        payment_count = Payment.objects.filter(booking=self.booking).count()
        self.assertEqual(payment_count, 2)

    @patch('payments.services.payment_service.stripe.checkout.Session.create')
    def test_create_checkout_session_organizer_publishes_event(self, mock_stripe_create):
        """Should auto-publish event when organizer completes payment."""
        # Create event in DRAFT status
        draft_event = Event.objects.create(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="Draft Event",
            difficulty="easy",
            datetime_start=timezone.now() + timedelta(days=2),
            price_cents=0,
            status="DRAFT",
        )

        booking = Booking.objects.create(
            user=self.user,
            event=draft_event,
            amount_cents=0,
            status=BookingStatus.PENDING,
        )

        # Create zero-amount checkout (auto-confirms)
        PaymentService.create_checkout_session(
            booking=booking,
            user=self.user,
            success_url="http://example.com/success",
            cancel_url="http://example.com/cancel",
        )

        # Verify booking confirmed
        booking.refresh_from_db()
        self.assertEqual(booking.status, BookingStatus.CONFIRMED)

        # Verify event published (organizer paid)
        draft_event.refresh_from_db()
        self.assertEqual(draft_event.status, "PUBLISHED")
