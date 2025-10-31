"""
Tests for payment validators.

Tests business rule validation for payments, refunds, and Stripe integration.
"""

from datetime import timedelta
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings

from languages.models import Language
from partners.models import Partner
from events.models import Event
from bookings.models import Booking, BookingStatus
from payments.models import Payment
from payments.validators import (
    validate_stripe_test_mode,
    validate_booking_is_payable,
    validate_payment_retry_limit,
    validate_refund_eligibility,
    validate_stripe_webhook_signature,
)
from payments.constants import (
    MAX_PAYMENT_RETRIES,
    REFUND_DEADLINE_HOURS,
    STATUS_SUCCEEDED,
    STATUS_PENDING,
)

User = get_user_model()


class StripeTestModeValidatorTest(TestCase):
    """Test Stripe TEST mode enforcement."""

    @patch('payments.validators.settings')
    def test_validate_test_mode_succeeds_with_test_key(self, mock_settings):
        """Should pass when STRIPE_SECRET_KEY starts with sk_test_."""
        mock_settings.STRIPE_SECRET_KEY = "sk_test_123456789"

        # Should not raise
        validate_stripe_test_mode()

    @patch('payments.validators.settings')
    def test_validate_test_mode_fails_with_live_key(self, mock_settings):
        """Should raise ValidationError when using live key."""
        mock_settings.STRIPE_SECRET_KEY = "sk_live_123456789"

        with self.assertRaises(ValidationError) as cm:
            validate_stripe_test_mode()

        self.assertIn("TEST mode required", str(cm.exception))

    @patch('payments.validators.settings')
    @patch('payments.validators.REQUIRE_TEST_MODE', False)
    def test_validate_test_mode_skipped_when_disabled(self, mock_settings):
        """Should skip validation when REQUIRE_TEST_MODE is False."""
        mock_settings.STRIPE_SECRET_KEY = "sk_live_123456789"

        # Should not raise even with live key
        validate_stripe_test_mode()


class BookingPayableValidatorTest(TestCase):
    """Test booking payability validation."""

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

    def test_validate_pending_booking_is_payable(self):
        """Should pass for PENDING booking."""
        booking = Booking.objects.create(
            user=self.user,
            event=self.event,
            amount_cents=700,
            status=BookingStatus.PENDING,
        )

        # Should not raise
        validate_booking_is_payable(booking)

    def test_validate_confirmed_booking_not_payable(self):
        """Should raise ValidationError for CONFIRMED booking."""
        booking = Booking.objects.create(
            user=self.user,
            event=self.event,
            amount_cents=700,
            status=BookingStatus.CONFIRMED,
        )

        with self.assertRaises(ValidationError) as cm:
            validate_booking_is_payable(booking)

        self.assertIn("not payable", str(cm.exception))

    def test_validate_cancelled_booking_not_payable(self):
        """Should raise ValidationError for CANCELLED booking."""
        booking = Booking.objects.create(
            user=self.user,
            event=self.event,
            amount_cents=700,
            status=BookingStatus.CANCELLED,
        )

        with self.assertRaises(ValidationError) as cm:
            validate_booking_is_payable(booking)

        self.assertIn("not payable", str(cm.exception))

    def test_validate_expired_booking_gets_cancelled(self):
        """Should auto-cancel expired booking and raise ValidationError."""
        booking = Booking.objects.create(
            user=self.user,
            event=self.event,
            amount_cents=700,
            status=BookingStatus.PENDING,
            expires_at=timezone.now() - timedelta(minutes=1),  # Expired
        )

        with self.assertRaises(ValidationError) as cm:
            validate_booking_is_payable(booking)

        self.assertIn("expired", str(cm.exception))

        # Check booking was cancelled
        booking.refresh_from_db()
        self.assertEqual(booking.status, BookingStatus.CANCELLED)


class PaymentRetryLimitValidatorTest(TestCase):
    """Test payment retry limit enforcement."""

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
        self.booking = Booking.objects.create(
            user=self.user,
            event=self.event,
            amount_cents=700,
            status=BookingStatus.PENDING,
        )

    def test_validate_retry_limit_succeeds_with_few_attempts(self):
        """Should pass when payment count is below limit."""
        # Create 2 failed payments (below limit of 3)
        for i in range(2):
            Payment.objects.create(
                user=self.user,
                booking=self.booking,
                amount_cents=700,
                status=STATUS_PENDING,
            )

        # Should not raise
        validate_payment_retry_limit(self.booking)

    def test_validate_retry_limit_fails_at_max_attempts(self):
        """Should raise ValidationError when retry limit reached."""
        # Create MAX_PAYMENT_RETRIES payments
        for i in range(MAX_PAYMENT_RETRIES):
            Payment.objects.create(
                user=self.user,
                booking=self.booking,
                amount_cents=700,
                status=STATUS_PENDING,
            )

        with self.assertRaises(ValidationError) as cm:
            validate_payment_retry_limit(self.booking)

        self.assertIn("retry limit exceeded", str(cm.exception))
        self.assertIn(str(MAX_PAYMENT_RETRIES), str(cm.exception))


class RefundEligibilityValidatorTest(TestCase):
    """Test refund eligibility validation."""

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

    def test_validate_confirmed_booking_before_deadline(self):
        """Should pass for CONFIRMED booking 4h before event."""
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

        # Should not raise
        validate_refund_eligibility(booking)

    def test_validate_pending_booking_not_eligible(self):
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
            validate_refund_eligibility(booking)

        self.assertIn("CONFIRMED", str(cm.exception))

    def test_validate_cancelled_booking_not_eligible(self):
        """Should raise ValidationError for CANCELLED booking."""
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
            validate_refund_eligibility(booking)

        self.assertIn("already cancelled", str(cm.exception))

    def test_validate_refund_deadline_passed(self):
        """Should raise ValidationError when within 3h of event."""
        event = Event.objects.create(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="Test Event",
            difficulty="easy",
            datetime_start=timezone.now() + timedelta(hours=2),  # Only 2h away
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

        self.assertIn(f"{REFUND_DEADLINE_HOURS}h", str(cm.exception))

    def test_validate_event_already_started(self):
        """Should raise ValidationError for event that already started."""
        event = Event.objects.create(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="Test Event",
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


class StripeWebhookValidatorTest(TestCase):
    """Test Stripe webhook signature validation."""

    @patch('stripe.Webhook.construct_event')
    def test_validate_webhook_signature_succeeds(self, mock_construct):
        """Should return event when signature is valid."""
        expected_event = {"type": "checkout.session.completed", "data": {}}
        mock_construct.return_value = expected_event

        result = validate_stripe_webhook_signature(
            payload=b'{"test": "data"}',
            sig_header="t=123,v1=abc",
            webhook_secret="whsec_test123"
        )

        self.assertEqual(result, expected_event)
        mock_construct.assert_called_once()

    @patch('stripe.Webhook.construct_event')
    def test_validate_webhook_signature_fails(self, mock_construct):
        """Should raise ValidationError when signature is invalid."""
        import stripe
        mock_construct.side_effect = stripe.error.SignatureVerificationError(
            "Invalid signature", "sig_header"
        )

        with self.assertRaises(ValidationError) as cm:
            validate_stripe_webhook_signature(
                payload=b'{"test": "data"}',
                sig_header="invalid",
                webhook_secret="whsec_test123"
            )

        self.assertIn("Invalid webhook signature", str(cm.exception))
