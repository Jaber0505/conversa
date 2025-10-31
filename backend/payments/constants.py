"""
Payment-specific constants.

Defines constants for Stripe integration, payment statuses, and business rules.
"""

# ==============================================================================
# STRIPE CONFIGURATION
# ==============================================================================

# Default currency for payments
DEFAULT_PAYMENT_CURRENCY = "EUR"

# Stripe mode enforcement
REQUIRE_TEST_MODE = True  # Force sk_test_ keys only (no real money)

# Default redirect paths (if not provided by frontend)
DEFAULT_SUCCESS_PATH = "/stripe/success"
DEFAULT_CANCEL_PATH = "/stripe/cancel"

# ==============================================================================
# PAYMENT BUSINESS RULES
# ==============================================================================

# One booking = one seat (no quantity support)
BOOKING_QUANTITY = 1

# Payment retry limits
MAX_PAYMENT_RETRIES = 3  # Maximum payment attempts per booking

# Refund deadline (must match booking cancellation deadline)
REFUND_DEADLINE_HOURS = 3  # Cannot refund after this time before event

# ==============================================================================
# STRIPE WEBHOOK EVENTS
# ==============================================================================

# Events we handle
WEBHOOK_EVENT_CHECKOUT_COMPLETED = "checkout.session.completed"
WEBHOOK_EVENT_PAYMENT_FAILED = "payment_intent.payment_failed"
WEBHOOK_EVENT_SESSION_EXPIRED = "checkout.session.expired"

# ==============================================================================
# PAYMENT STATUS CHOICES
# ==============================================================================

# These match Payment.PaymentStatus model choices
STATUS_PENDING = "pending"
STATUS_SUCCEEDED = "succeeded"
STATUS_FAILED = "failed"
STATUS_CANCELED = "canceled"
