"""
Tests for payment API views.

Tests Stripe Checkout session creation and webhook handling.
"""

from datetime import timedelta
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from languages.models import Language
from partners.models import Partner
from events.models import Event
from bookings.models import Booking, BookingStatus
from payments.models import Payment
from payments.constants import (
    STATUS_PENDING,
    STATUS_SUCCEEDED,
    MAX_PAYMENT_RETRIES,
)

User = get_user_model()


class CreateCheckoutSessionViewTest(TestCase):
    """Test suite for CreateCheckoutSessionView."""

    def setUp(self):
        """Create test fixtures."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            age=25,
            consent_given=True,
        )
        self.client.force_authenticate(user=self.user)

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

        self.url = reverse('payments:create-checkout-session')

    @patch('payments.services.payment_service.stripe.checkout.Session.create')
    @patch('payments.services.payment_service.AuditService.log_payment_created')
    def test_create_checkout_session_success(self, mock_audit, mock_stripe_create):
        """Should create Stripe checkout session and return URL."""
        # Mock Stripe response
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/session123"
        mock_session.id = "cs_test_123"
        mock_stripe_create.return_value = mock_session

        # Make request
        response = self.client.post(self.url, {
            "booking_public_id": str(self.booking.public_id),
            "lang": "fr",
        })

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("url", response.data)
        self.assertIn("session_id", response.data)
        self.assertEqual(response.data["url"], "https://checkout.stripe.com/session123")
        self.assertEqual(response.data["session_id"], "cs_test_123")

        # Verify payment created
        payment = Payment.objects.filter(booking=self.booking).first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.status, STATUS_PENDING)

    def test_create_checkout_session_unauthenticated(self):
        """Should return 401 for unauthenticated user."""
        self.client.force_authenticate(user=None)

        response = self.client.post(self.url, {
            "booking_public_id": str(self.booking.public_id),
            "lang": "fr",
        })

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_checkout_session_not_users_booking(self):
        """Should return 404 when booking doesn't belong to user."""
        other_user = User.objects.create_user(
            email="other@example.com",
            password="pass",
            age=25,
            consent_given=True,
        )
        self.client.force_authenticate(user=other_user)

        response = self.client.post(self.url, {
            "booking_public_id": str(self.booking.public_id),
            "lang": "fr",
        })

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_checkout_session_confirmed_booking(self):
        """Should return 409 for already CONFIRMED booking."""
        self.booking.status = BookingStatus.CONFIRMED
        self.booking.save()

        response = self.client.post(self.url, {
            "booking_public_id": str(self.booking.public_id),
            "lang": "fr",
        })

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("not payable", str(response.data))

    def test_create_checkout_session_retry_limit_exceeded(self):
        """Should return 409 when payment retry limit exceeded."""
        # Create max payment attempts
        for i in range(MAX_PAYMENT_RETRIES):
            Payment.objects.create(
                user=self.user,
                booking=self.booking,
                amount_cents=700,
                status=STATUS_PENDING,
            )

        response = self.client.post(self.url, {
            "booking_public_id": str(self.booking.public_id),
            "lang": "fr",
        })

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("retry limit", str(response.data))

    @patch('payments.services.payment_service.AuditService.log_payment_succeeded')
    def test_create_checkout_session_zero_amount(self, mock_audit):
        """Should handle zero-amount booking without Stripe."""
        self.booking.amount_cents = 0
        self.booking.save()

        response = self.client.post(self.url, {
            "booking_public_id": str(self.booking.public_id),
            "lang": "fr",
        })

        # Should return 201 but without Stripe URL
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Zero-amount returns None for url/session_id
        self.assertIsNone(response.data.get("url"))
        self.assertIsNone(response.data.get("session_id"))

        # Verify booking auto-confirmed
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, BookingStatus.CONFIRMED)

    def test_create_checkout_session_invalid_booking_id(self):
        """Should return 404 for non-existent booking."""
        response = self.client.post(self.url, {
            "booking_public_id": "00000000-0000-0000-0000-000000000000",
            "lang": "fr",
        })

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_checkout_session_missing_params(self):
        """Should return 400 for missing required fields."""
        response = self.client.post(self.url, {
            "lang": "fr",
            # Missing booking_public_id
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('payments.services.payment_service.stripe.checkout.Session.create')
    @patch('payments.services.payment_service.AuditService.log_payment_created')
    def test_create_checkout_session_with_custom_urls(self, mock_audit, mock_stripe_create):
        """Should use custom success/cancel URLs when provided."""
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/session123"
        mock_session.id = "cs_test_123"
        mock_stripe_create.return_value = mock_session

        response = self.client.post(self.url, {
            "booking_public_id": str(self.booking.public_id),
            "lang": "fr",
            "success_url": "https://custom.com/success",
            "cancel_url": "https://custom.com/cancel",
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify Stripe was called with custom URLs
        call_kwargs = mock_stripe_create.call_args[1]
        self.assertIn("custom.com/success", call_kwargs['success_url'])
        self.assertIn("custom.com/cancel", call_kwargs['cancel_url'])


class StripeWebhookViewTest(TestCase):
    """Test suite for StripeWebhookView."""

    def setUp(self):
        """Create test fixtures."""
        self.client = APIClient()
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
        self.payment = Payment.objects.create(
            user=self.user,
            booking=self.booking,
            amount_cents=700,
            status=STATUS_PENDING,
            stripe_session_id="cs_test_123",
        )

        self.url = reverse('payments:stripe-webhook')

    @patch('payments.validators.stripe.Webhook.construct_event')
    @patch('payments.services.payment_service.AuditService.log_payment_succeeded')
    def test_webhook_checkout_completed(self, mock_audit, mock_construct):
        """Should confirm booking on checkout.session.completed."""
        # Mock webhook event
        mock_event = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_123",
                    "payment_intent": "pi_test_456",
                    "metadata": {
                        "booking_public_id": str(self.booking.public_id),
                    }
                }
            }
        }
        mock_construct.return_value = mock_event

        # Send webhook
        response = self.client.post(
            self.url,
            data=b'{"test": "data"}',
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="t=123,v1=abc",
        )

        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify booking confirmed
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, BookingStatus.CONFIRMED)

        # Verify payment updated
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, STATUS_SUCCEEDED)

        # Verify audit log
        mock_audit.assert_called_once()

    @patch('payments.validators.stripe.Webhook.construct_event')
    @patch('payments.services.payment_service.AuditService.log_payment_failed')
    def test_webhook_payment_failed(self, mock_audit, mock_construct):
        """Should mark payment as failed on payment_intent.payment_failed."""
        mock_event = {
            "type": "payment_intent.payment_failed",
            "data": {
                "object": {
                    "id": "pi_test_456",
                    "last_payment_error": {
                        "message": "Insufficient funds"
                    },
                    "metadata": {
                        "stripe_session_id": "cs_test_123",
                    }
                }
            }
        }
        mock_construct.return_value = mock_event

        response = self.client.post(
            self.url,
            data=b'{"test": "data"}',
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="t=123,v1=abc",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify payment marked as failed
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, "failed")

        # Verify audit log
        mock_audit.assert_called_once()

    @patch('payments.validators.stripe.Webhook.construct_event')
    def test_webhook_session_expired(self, mock_construct):
        """Should handle checkout.session.expired event."""
        mock_event = {
            "type": "checkout.session.expired",
            "data": {
                "object": {
                    "id": "cs_test_123",
                }
            }
        }
        mock_construct.return_value = mock_event

        response = self.client.post(
            self.url,
            data=b'{"test": "data"}',
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="t=123,v1=abc",
        )

        # Should acknowledge event
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('payments.validators.stripe.Webhook.construct_event')
    def test_webhook_unknown_event_type(self, mock_construct):
        """Should acknowledge unknown event types without processing."""
        mock_event = {
            "type": "customer.created",
            "data": {"object": {}}
        }
        mock_construct.return_value = mock_event

        response = self.client.post(
            self.url,
            data=b'{"test": "data"}',
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="t=123,v1=abc",
        )

        # Should acknowledge but not process
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('payments.validators.stripe.Webhook.construct_event')
    def test_webhook_invalid_signature(self, mock_construct):
        """Should return 400 for invalid webhook signature."""
        import stripe
        mock_construct.side_effect = stripe.error.SignatureVerificationError(
            "Invalid signature", "sig_header"
        )

        response = self.client.post(
            self.url,
            data=b'{"test": "data"}',
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="invalid",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid webhook signature", str(response.data))

    @patch('payments.validators.stripe.Webhook.construct_event')
    def test_webhook_missing_signature_header(self, mock_construct):
        """Should return 400 when Stripe-Signature header is missing."""
        response = self.client.post(
            self.url,
            data=b'{"test": "data"}',
            content_type="application/json",
            # No HTTP_STRIPE_SIGNATURE header
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('payments.validators.stripe.Webhook.construct_event')
    @patch('payments.services.payment_service.AuditService.log_payment_succeeded')
    def test_webhook_idempotency(self, mock_audit, mock_construct):
        """Should handle duplicate webhook events gracefully."""
        mock_event = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_123",
                    "payment_intent": "pi_test_456",
                    "metadata": {
                        "booking_public_id": str(self.booking.public_id),
                    }
                }
            }
        }
        mock_construct.return_value = mock_event

        # First webhook
        response1 = self.client.post(
            self.url,
            data=b'{"test": "data"}',
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="t=123,v1=abc",
        )
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        # Duplicate webhook (should not cause errors)
        response2 = self.client.post(
            self.url,
            data=b'{"test": "data"}',
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="t=123,v1=abc",
        )
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        # Verify booking still confirmed (not double-confirmed)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, BookingStatus.CONFIRMED)
