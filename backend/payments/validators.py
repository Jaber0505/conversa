"""
Payment validators.

Validates payment-related business rules before processing.
"""
from django.core.exceptions import ValidationError
from django.conf import settings

from .constants import REQUIRE_TEST_MODE, MAX_PAYMENT_RETRIES


def validate_stripe_test_mode():
    """
    Validate that Stripe is in TEST mode.

    Business Rule:
        Application only accepts TEST keys (sk_test_...).
        No real money transactions allowed.

    Raises:
        ValidationError: If not in test mode
    """
    if not REQUIRE_TEST_MODE:
        return  # Test mode not required

    key = getattr(settings, "STRIPE_SECRET_KEY", "")
    if not key.startswith("sk_test_"):
        raise ValidationError(
            "Stripe TEST mode required. STRIPE_SECRET_KEY must start with 'sk_test_'."
        )


def validate_booking_is_payable(booking):
    """
    Validate that a booking can be paid.

    Business Rules:
        - Booking must be PENDING
        - Booking must not be expired
        - User must be the booking owner (checked in view)

    Args:
        booking: Booking instance

    Raises:
        ValidationError: If booking cannot be paid
    """
    from bookings.models import BookingStatus

    # Check if expired (and auto-cancel if so)
    if hasattr(booking, "soft_cancel_if_expired") and booking.soft_cancel_if_expired():
        raise ValidationError("Booking has expired and was cancelled.")

    # Check status
    if booking.status != BookingStatus.PENDING:
        raise ValidationError(
            f"Booking is not payable. Current status: {booking.status}"
        )


def validate_payment_retry_limit(booking):
    """
    Validate that booking hasn't exceeded payment retry limit.

    Business Rule:
        Maximum MAX_PAYMENT_RETRIES payment attempts per booking.

    Args:
        booking: Booking instance

    Raises:
        ValidationError: If retry limit exceeded
    """
    from .models import Payment

    payment_count = Payment.objects.filter(booking=booking).count()

    if payment_count >= MAX_PAYMENT_RETRIES:
        raise ValidationError(
            f"Payment retry limit exceeded ({MAX_PAYMENT_RETRIES} attempts). "
            "Please contact support."
        )


def validate_refund_eligibility(booking):
    """
    Validate that a booking is eligible for refund.

    Business Rules:
        - Booking must be CONFIRMED
        - Event must not have started
        - Must be at least REFUND_DEADLINE_HOURS before event

    Args:
        booking: Booking instance

    Raises:
        ValidationError: If refund not allowed
    """
    from django.utils import timezone
    from datetime import timedelta
    from bookings.models import BookingStatus
    from .constants import REFUND_DEADLINE_HOURS

    # Must be confirmed
    if booking.status != BookingStatus.CONFIRMED:
        raise ValidationError(
            f"Only CONFIRMED bookings can be refunded. Current status: {booking.status}"
        )

    # Check deadline
    event = booking.event
    deadline = event.datetime_start - timedelta(hours=REFUND_DEADLINE_HOURS)

    if timezone.now() >= deadline:
        raise ValidationError(
            f"Refund not allowed. Must cancel at least {REFUND_DEADLINE_HOURS}h before event."
        )

    # Event must not have started
    if timezone.now() >= event.datetime_start:
        raise ValidationError("Cannot refund a booking for an event that has already started.")


def validate_stripe_webhook_signature(payload, sig_header, webhook_secret):
    """
    Validate Stripe webhook signature.

    Args:
        payload: Request body (bytes)
        sig_header: Stripe-Signature header value
        webhook_secret: Webhook secret from settings

    Returns:
        dict: Verified Stripe event

    Raises:
        ValidationError: If signature invalid
    """
    import stripe

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=webhook_secret
        )
        return event
    except stripe.error.SignatureVerificationError:
        raise ValidationError("Invalid webhook signature")
    except ValueError:
        raise ValidationError("Invalid webhook payload")
    except Exception as e:
        raise ValidationError(f"Webhook validation failed: {str(e)}")
