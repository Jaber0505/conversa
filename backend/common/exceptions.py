"""
Custom exceptions for business logic errors.

These exceptions provide clear, consistent error handling across the application.
"""

from rest_framework.exceptions import APIException
from rest_framework import status


class BusinessRuleViolation(APIException):
    """Base exception for business rule violations."""
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Business rule violation."
    default_code = "business_rule_violation"


class EventFullError(BusinessRuleViolation):
    """Raised when trying to book a full event."""
    default_detail = "Event is full. Maximum 6 participants allowed."
    default_code = "event_full"


class InsufficientCapacityError(BusinessRuleViolation):
    """Raised when partner venue has insufficient capacity."""
    default_detail = "Partner venue has insufficient capacity for this time slot."
    default_code = "insufficient_capacity"


class CancellationDeadlineError(BusinessRuleViolation):
    """Raised when trying to cancel within CANCELLATION_DEADLINE_HOURS (3h) of event start."""
    default_detail = "Cannot cancel booking within 3 hours of event start."
    default_code = "cancellation_deadline_passed"


class BookingExpiredError(BusinessRuleViolation):
    """Raised when booking has expired."""
    default_detail = "Booking has expired."
    default_code = "booking_expired"


class EventAlreadyCancelledError(BusinessRuleViolation):
    """Raised when trying to cancel an already cancelled event."""
    default_detail = "Event is already cancelled."
    default_code = "event_already_cancelled"


class BookingAlreadyConfirmedError(BusinessRuleViolation):
    """Raised when trying to modify a confirmed booking."""
    default_detail = "Booking is already confirmed and cannot be modified."
    default_code = "booking_already_confirmed"
