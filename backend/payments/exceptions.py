"""
Custom exceptions for payments module.

Provides specific exception types for payment and refund operations.
"""


class PaymentError(Exception):
    """Base exception for all payment-related errors."""
    pass


class StripeError(PaymentError):
    """Stripe API error (wrapper for stripe.error.StripeError)."""
    pass


class RefundError(PaymentError):
    """Base exception for refund-related errors."""
    pass


class RefundNotEligibleError(RefundError):
    """Booking not eligible for refund (already refunded, too late, etc.)."""
    pass


class RefundProcessingError(RefundError):
    """Error occurred while processing refund with Stripe."""
    pass


class PaymentIntentMissingError(RefundError):
    """Payment intent ID missing - cannot process refund."""
    pass


class InvalidCurrencyError(PaymentError):
    """Invalid currency code provided."""
    pass
