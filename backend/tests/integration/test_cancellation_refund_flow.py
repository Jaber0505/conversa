"""
Integration test: Complete cancellation and refund flow.

Tests end-to-end flow for booking cancellation with automatic Stripe refund.
"""

from datetime import timedelta
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError

from languages.models import Language
from partners.models import Partner
from events.models import Event
from bookings.models import Booking, BookingStatus
from bookings.services import BookingService
from payments.models import Payment
from payments.services import RefundService
from payments.constants import STATUS_SUCCEEDED

User = get_user_model()


class CompleteCancellationRefundFlowTest(TestCase):
    """
    Test complete end-to-end cancellation with refund:
    1. User creates booking
    2. User pays (Stripe) → CONFIRMED
    3. User cancels booking (before 3h deadline)
    4. Automatic Stripe refund processed
    5. Booking status → CANCELLED
    6. Refund payment record created
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
            capacity=50,
            is_active=True,
        )
        self.user = User.objects.create_user(
            email="user@example.com",
            password="pass",
            age=25,
            consent_given=True,
        )

        # Create event 4h in future (before 3h deadline)
        datetime_start = timezone.now() + timedelta(hours=4)
        datetime_start = datetime_start.replace(minute=0, second=0, microsecond=0)

        self.event = Event.objects.create(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="Test Event",
            difficulty="easy",
            datetime_start=datetime_start,
            status="PUBLISHED",
            price_cents=700,
        )

    def test_complete_cancellation_with_stripe_refund(self):
        """
        Full flow: Create booking → Pay → Cancel → Refund processed
        """
        # ==============================================
        # STEP 1: Create booking
        # ==============================================
        booking = Booking.objects.create(
            user=self.user,
            event=self.event,
            amount_cents=700,
            status=BookingStatus.PENDING,
        )
        self.assertEqual(booking.status, BookingStatus.PENDING)

        # ==============================================
        # STEP 2: Simulate payment (create confirmed booking)
        # ==============================================
        payment = Payment.objects.create(
            user=self.user,
            booking=booking,
            amount_cents=700,
            currency="EUR",
            status=STATUS_SUCCEEDED,
            stripe_payment_intent_id="pi_test_original_123",
            stripe_checkout_session_id="cs_test_456",
        )

        # Mark booking as confirmed
        booking.mark_confirmed(payment_intent_id="pi_test_original_123")
        self.assertEqual(booking.status, BookingStatus.CONFIRMED)

        # ==============================================
        # STEP 3: Cancel booking (triggers refund)
        # ==============================================
        with patch('payments.services.refund_service.stripe.Refund.create') as mock_refund:
            with patch('audit.services.AuditService.log_payment_refunded'):
                # Mock Stripe refund
                mock_refund_obj = MagicMock()
                mock_refund_obj.id = "re_test_789"
                mock_refund_obj.status = "succeeded"
                mock_refund.return_value = mock_refund_obj

                # Cancel booking via service (includes refund)
                result = BookingService.cancel_booking(
                    booking=booking,
                    cancelled_by=self.user
                )

        # ==============================================
        # VERIFICATION: Cancellation result
        # ==============================================
        self.assertTrue(result["cancelled"])
        self.assertTrue(result["refunded"])
        self.assertIn("re_test_789", result["refund_message"])

        # ==============================================
        # VERIFICATION: Booking status
        # ==============================================
        booking.refresh_from_db()
        self.assertEqual(booking.status, BookingStatus.CANCELLED)
        self.assertIsNotNone(booking.cancelled_at)

        # ==============================================
        # VERIFICATION: Refund payment record
        # ==============================================
        refund_payment = Payment.objects.filter(
            booking=booking,
            amount_cents__lt=0  # Negative amount = refund
        ).first()

        self.assertIsNotNone(refund_payment)
        self.assertEqual(refund_payment.amount_cents, -700)  # Negative
        self.assertEqual(refund_payment.status, STATUS_SUCCEEDED)
        self.assertEqual(refund_payment.user, self.user)

        # ==============================================
        # VERIFICATION: Stripe API called correctly
        # ==============================================
        mock_refund.assert_called_once()
        call_kwargs = mock_refund.call_args[1]
        self.assertEqual(call_kwargs['payment_intent'], "pi_test_original_123")
        self.assertEqual(call_kwargs['metadata']['booking_public_id'], str(booking.public_id))

    def test_cancellation_free_booking_no_stripe_refund(self):
        """
        Free booking cancellation should skip Stripe.
        """
        # Create free booking
        booking = Booking.objects.create(
            user=self.user,
            event=self.event,
            amount_cents=0,  # Free!
            status=BookingStatus.CONFIRMED,
        )

        # Create zero-amount payment
        payment = Payment.objects.create(
            user=self.user,
            booking=booking,
            amount_cents=0,
            currency="EUR",
            status=STATUS_SUCCEEDED,
        )

        # Cancel booking
        with patch('audit.services.AuditService.log_payment_refunded'):
            result = BookingService.cancel_booking(
                booking=booking,
                cancelled_by=self.user
            )

        # Should succeed without Stripe
        self.assertTrue(result["cancelled"])
        self.assertTrue(result["refunded"])
        self.assertIn("Free booking", result["refund_message"])

        # Verify refund payment created (zero amount)
        # Note: For free bookings, we create a second Payment record with amount_cents=0
        all_payments = list(Payment.objects.filter(booking=booking).order_by('created_at'))
        self.assertEqual(len(all_payments), 2)  # Original + refund

        refund_payment = all_payments[1]  # Second payment is the refund
        self.assertIsNotNone(refund_payment)
        self.assertEqual(refund_payment.amount_cents, 0)

    def test_cancellation_within_deadline_fails(self):
        """
        Cancellation within 3h of event should fail.
        """
        # Create event only 2h in future (within 3h deadline)
        event_soon = Event.objects.create(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="Soon Event",
            difficulty="easy",
            datetime_start=timezone.now() + timedelta(hours=2),
            status="PUBLISHED",
        )

        booking = Booking.objects.create(
            user=self.user,
            event=event_soon,
            amount_cents=700,
            status=BookingStatus.CONFIRMED,
        )

        # Try to cancel (should fail - within deadline)
        from common.exceptions import CancellationDeadlineError
        with self.assertRaises(CancellationDeadlineError) as cm:
            BookingService.cancel_booking(
                booking=booking,
                cancelled_by=self.user
            )

        self.assertIn("3", str(cm.exception))

        # Booking should still be CONFIRMED
        booking.refresh_from_db()
        self.assertEqual(booking.status, BookingStatus.CONFIRMED)


class RefundFailureHandlingTest(TestCase):
    """
    Test refund failure scenarios.
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
            capacity=50,
            is_active=True,
        )
        self.user = User.objects.create_user(
            email="user@example.com",
            password="pass",
            age=25,
            consent_given=True,
        )

        datetime_start = timezone.now() + timedelta(hours=4)
        self.event = Event.objects.create(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="Test Event",
            difficulty="easy",
            datetime_start=datetime_start,
            status="PUBLISHED",
        )

    def test_stripe_refund_failure_prevents_cancellation(self):
        """
        If Stripe refund fails, booking should NOT be cancelled.
        """
        booking = Booking.objects.create(
            user=self.user,
            event=self.event,
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

        # Mock Stripe refund failure
        with patch('payments.services.refund_service.stripe.Refund.create') as mock_refund:
            # Create a mock exception that simulates Stripe error
            mock_error = Exception("Stripe error: Charge already refunded")
            mock_refund.side_effect = mock_error

            # Cancel should raise error
            with self.assertRaises(Exception):
                BookingService.cancel_booking(
                    booking=booking,
                    cancelled_by=self.user
                )

        # Booking should still be CONFIRMED (transaction rolled back)
        booking.refresh_from_db()
        self.assertEqual(booking.status, BookingStatus.CONFIRMED)

    def test_refund_without_payment_intent_id_fails(self):
        """
        Refund should fail gracefully if payment has no payment_intent_id.
        """
        booking = Booking.objects.create(
            user=self.user,
            event=self.event,
            amount_cents=700,
            status=BookingStatus.CONFIRMED,
        )

        # Payment without payment_intent_id
        Payment.objects.create(
            user=self.user,
            booking=booking,
            amount_cents=700,
            status=STATUS_SUCCEEDED,
            stripe_payment_intent_id=None,  # Missing!
        )

        # Try to cancel booking (which will attempt refund)
        # Should raise ValidationError due to missing payment_intent_id
        with self.assertRaises(ValidationError) as ctx:
            BookingService.cancel_booking(
                booking=booking,
                cancelled_by=self.user
            )

        # Error message should mention payment intent
        error_msg = str(ctx.exception).lower()
        self.assertTrue(
            "payment_intent_id" in error_msg or "payment intent" in error_msg,
            f"Expected payment intent error, got: {ctx.exception}"
        )


class PendingBookingCancellationTest(TestCase):
    """
    Test cancellation of PENDING bookings (not paid yet).
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
            capacity=50,
            is_active=True,
        )
        self.user = User.objects.create_user(
            email="user@example.com",
            password="pass",
            age=25,
            consent_given=True,
        )

        datetime_start = timezone.now() + timedelta(hours=4)
        self.event = Event.objects.create(
            organizer=self.user,
            partner=self.partner,
            language=self.language,
            theme="Test Event",
            difficulty="easy",
            datetime_start=datetime_start,
            status="PUBLISHED",
        )

    def test_pending_booking_cancellation_no_refund(self):
        """
        PENDING booking cancellation should NOT trigger refund (not paid).
        """
        booking = Booking.objects.create(
            user=self.user,
            event=self.event,
            amount_cents=700,
            status=BookingStatus.PENDING,
        )

        # Cancel booking
        result = BookingService.cancel_booking(
            booking=booking,
            cancelled_by=self.user
        )

        # Should cancel without refund
        self.assertTrue(result["cancelled"])
        self.assertFalse(result["refunded"])  # No refund for PENDING
        self.assertIsNone(result["refund_message"])

        # Verify cancelled
        booking.refresh_from_db()
        self.assertEqual(booking.status, BookingStatus.CANCELLED)

        # Verify no refund payment created
        refund_count = Payment.objects.filter(
            booking=booking,
            amount_cents__lt=0
        ).count()
        self.assertEqual(refund_count, 0)
