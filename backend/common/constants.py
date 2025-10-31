"""
Common constants used across the entire application.

This module defines app-wide constants to avoid magic numbers and ensure
consistency across all modules. All modules should import from here.
"""

# ==============================================================================
# EVENT CONSTANTS
# ==============================================================================

# Event pricing
DEFAULT_EVENT_PRICE_CENTS = 700  # 7.00 EUR
DEFAULT_CURRENCY = "EUR"

# Event participation limits
MAX_PARTICIPANTS_PER_EVENT = 6
MIN_PARTICIPANTS_PER_EVENT = 3

# Event duration
DEFAULT_EVENT_DURATION_HOURS = 1  # All events are exactly 1 hour long

# Event scheduling constraints
MIN_ADVANCE_BOOKING_HOURS = 24  # Events must be created at least 24h in advance (no same-day events)
MAX_FUTURE_BOOKING_DAYS = 7  # Events cannot be scheduled more than 1 week in advance

# ==============================================================================
# BOOKING CONSTANTS
# ==============================================================================

# Booking time limits
BOOKING_TTL_MINUTES = 15  # Booking expiration time (PENDING → CANCELLED)
CANCELLATION_DEADLINE_HOURS = 3  # Cannot cancel within 3h of event start
AUTO_CANCEL_CHECK_HOURS = 1  # Auto-cancel if < min participants 1h before event

# ==============================================================================
# PARTNER CONSTANTS
# ==============================================================================

# Partner capacity constraints
DEFAULT_PARTNER_CAPACITY = 50  # Default capacity for new partner venues
MIN_PARTNER_CAPACITY = 10  # Minimum capacity (must host at least one full event)
MAX_PARTNER_CAPACITY = 200  # Maximum reasonable capacity for a venue

# Partner reputation
MIN_PARTNER_REPUTATION = 0.0
MAX_PARTNER_REPUTATION = 5.0

# Partner API
PARTNER_API_KEY_LENGTH = 64  # Length of generated API keys (hex characters)

# ==============================================================================
# USER CONSTANTS
# ==============================================================================

# User age restrictions
MINIMUM_USER_AGE = 18  # Minimum age to register

# Password rules
MIN_USER_PASSWORD_LENGTH = 9  # Minimum password length

# Profile limits
MAX_USER_BIO_LENGTH = 500  # Maximum bio text length

# Language requirements
REQUIRED_NATIVE_LANGUAGES = 1  # At least 1 native language required
REQUIRED_TARGET_LANGUAGES = 1  # At least 1 target language required

# ==============================================================================
# AUDIT & LOGGING
# ==============================================================================

# Audit log retention policies (in days)
# NOTE: Render Free Tier has 90-day automatic data retention limit
# For production with paid tier, increase these values

import os

# Check if running on Render Free Tier (limited storage)
IS_RENDER_FREE = os.environ.get('RENDER_FREE_TIER', 'false').lower() == 'true'

if IS_RENDER_FREE:
    # Render Free Tier: All logs limited to 30 days (stay well under 90-day limit)
    AUDIT_RETENTION_HTTP = 7          # HTTP requests: 7 days (save space)
    AUDIT_RETENTION_AUTH = 30         # Auth events: 30 days
    AUDIT_RETENTION_BUSINESS = 30     # Business events: 30 days
    AUDIT_RETENTION_ERROR = 30        # Errors: 30 days
    AUDIT_RETENTION_DEFAULT = 14      # Default: 14 days
else:
    # Production/Paid Tier: Industry-standard retention
    AUDIT_RETENTION_HTTP = 90         # HTTP requests: 3 months (operational)
    AUDIT_RETENTION_AUTH = 365        # Auth events: 1 year (security/compliance)
    AUDIT_RETENTION_BUSINESS = 2555   # Business events (payment/booking): 7 years (legal/accounting)
    AUDIT_RETENTION_ERROR = 365       # Errors: 1 year (debugging/analysis)
    AUDIT_RETENTION_DEFAULT = 180     # Default: 6 months (other categories)

# ==============================================================================
# PAGINATION
# ==============================================================================

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
