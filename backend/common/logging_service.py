"""
Centralized logging service for backend operations.

Provides structured logging for production debugging and monitoring.
All logs are output to console and can be viewed via Render's log viewer.
"""

import logging
import traceback
from typing import Any, Dict, Optional
from django.contrib.auth import get_user_model

User = get_user_model()


class LoggingService:
    """Centralized logging service for backend operations."""

    @staticmethod
    def _get_logger(name: str = "conversa") -> logging.Logger:
        """Get logger instance."""
        return logging.getLogger(name)

    @staticmethod
    def log_info(message: str, category: str = "general", extra: Optional[Dict[str, Any]] = None):
        """
        Log informational message.

        Args:
            message: The log message
            category: Category for organizing logs (e.g., "event", "payment", "booking")
            extra: Additional context data
        """
        logger = LoggingService._get_logger(category)
        extra_str = f" | Extra: {extra}" if extra else ""
        logger.info(f"[{category.upper()}] {message}{extra_str}")

    @staticmethod
    def log_warning(message: str, category: str = "general", extra: Optional[Dict[str, Any]] = None):
        """
        Log warning message.

        Args:
            message: The log message
            category: Category for organizing logs
            extra: Additional context data
        """
        logger = LoggingService._get_logger(category)
        extra_str = f" | Extra: {extra}" if extra else ""
        logger.warning(f"[{category.upper()}] {message}{extra_str}")

    @staticmethod
    def log_error(
        message: str,
        category: str = "general",
        exception: Optional[Exception] = None,
        extra: Optional[Dict[str, Any]] = None,
        user: Optional[User] = None,
    ):
        """
        Log error message with optional exception traceback.

        Args:
            message: The log message
            category: Category for organizing logs
            exception: Exception object to log
            extra: Additional context data
            user: User associated with the error (if any)
        """
        logger = LoggingService._get_logger(category)

        # Build context
        context_parts = []
        if user:
            user_info = f"User={user.id} ({user.email})"
            context_parts.append(user_info)

        if extra:
            context_parts.append(f"Extra={extra}")

        context_str = " | ".join(context_parts)
        full_message = f"[{category.upper()}] {message}"
        if context_str:
            full_message += f" | {context_str}"

        # Log exception with traceback
        if exception:
            logger.error(full_message, exc_info=exception)
            # Also log the full traceback explicitly
            tb = traceback.format_exc()
            logger.error(f"Traceback:\n{tb}")
        else:
            logger.error(full_message)

    @staticmethod
    def log_event_creation_start(user: User, event_data: Dict[str, Any]):
        """Log when event creation starts."""
        partner_name = getattr(event_data.get("partner"), "name", "Unknown")
        datetime_str = str(event_data.get("datetime_start"))

        LoggingService.log_info(
            f"🎯 Tentative de création d'événement par {user.email} - Lieu: {partner_name}, Date: {datetime_str}",
            category="event",
            extra={
                "user_id": user.id,
                "datetime_start": datetime_str,
                "partner_id": event_data.get("partner", {}).id if hasattr(event_data.get("partner"), "id") else event_data.get("partner"),
                "language": event_data.get("language", {}).code if hasattr(event_data.get("language"), "code") else event_data.get("language"),
            }
        )

    @staticmethod
    def log_event_creation_success(event, user: User):
        """Log successful event creation."""
        LoggingService.log_info(
            f"✅ Événement #{event.id} créé avec succès par {user.email} - Statut: {event.status}",
            category="event",
            extra={
                "event_id": event.id,
                "user_id": user.id,
                "status": event.status,
                "datetime_start": str(event.datetime_start),
            }
        )

    @staticmethod
    def log_event_creation_error(user: User, event_data: Dict[str, Any], exception: Exception):
        """Log event creation failure."""
        error_msg = str(exception)
        LoggingService.log_error(
            f"❌ ÉCHEC création événement pour {user.email} - Raison: {error_msg}",
            category="event",
            exception=exception,
            extra={
                "user_id": user.id,
                "event_data": event_data,
                "error_type": type(exception).__name__,
                "error_message": error_msg,
            },
            user=user,
        )

    @staticmethod
    def log_payment_creation_start(booking, user: User):
        """Log when payment creation starts."""
        LoggingService.log_info(
            f"Payment creation started for booking {booking.public_id}",
            category="payment",
            extra={
                "booking_id": str(booking.public_id),
                "user_id": user.id,
                "amount_cents": booking.amount_cents,
            }
        )

    @staticmethod
    def log_payment_creation_success(payment, booking, user: User):
        """Log successful payment creation."""
        LoggingService.log_info(
            f"Payment created successfully for booking {booking.public_id}",
            category="payment",
            extra={
                "payment_id": payment.id,
                "booking_id": str(booking.public_id),
                "user_id": user.id,
                "stripe_session_id": payment.stripe_checkout_session_id,
            }
        )

    @staticmethod
    def log_payment_creation_error(booking, user: User, exception: Exception):
        """Log payment creation failure."""
        LoggingService.log_error(
            f"Payment creation failed for booking {booking.public_id}",
            category="payment",
            exception=exception,
            extra={
                "booking_id": str(booking.public_id),
                "user_id": user.id,
                "error_type": type(exception).__name__,
            },
            user=user,
        )

    @staticmethod
    def log_booking_creation_start(user: User, event):
        """Log when booking creation starts."""
        LoggingService.log_info(
            f"Booking creation started for event {event.id}",
            category="booking",
            extra={
                "event_id": event.id,
                "user_id": user.id,
            }
        )

    @staticmethod
    def log_booking_creation_success(booking, user: User):
        """Log successful booking creation."""
        LoggingService.log_info(
            f"Booking {booking.public_id} created successfully",
            category="booking",
            extra={
                "booking_id": str(booking.public_id),
                "event_id": booking.event.id,
                "user_id": user.id,
                "status": booking.status,
            }
        )

    @staticmethod
    def log_booking_creation_error(event, user: User, exception: Exception):
        """Log booking creation failure."""
        LoggingService.log_error(
            f"Booking creation failed for event {event.id}",
            category="booking",
            exception=exception,
            extra={
                "event_id": event.id,
                "user_id": user.id,
                "error_type": type(exception).__name__,
            },
            user=user,
        )

    @staticmethod
    def log_validation_error(message: str, category: str, validation_errors: Dict[str, Any], user: Optional[User] = None):
        """Log validation errors."""
        user_email = user.email if user else "Anonymous"
        errors_str = ", ".join([f"{k}: {v}" for k, v in validation_errors.items()])

        LoggingService.log_warning(
            f"⚠️ Validation échouée pour {user_email} - {message} | Détails: {errors_str}",
            category=category,
            extra={
                "validation_errors": validation_errors,
                "user_id": user.id if user else None,
            }
        )

    @staticmethod
    def log_stripe_webhook_received(event_type: str, event_id: str):
        """Log Stripe webhook received."""
        LoggingService.log_info(
            f"Stripe webhook received: {event_type}",
            category="stripe",
            extra={
                "event_type": event_type,
                "event_id": event_id,
            }
        )

    @staticmethod
    def log_stripe_webhook_error(event_type: str, exception: Exception, extra: Optional[Dict[str, Any]] = None):
        """Log Stripe webhook processing error."""
        LoggingService.log_error(
            f"Stripe webhook processing failed: {event_type}",
            category="stripe",
            exception=exception,
            extra=extra,
        )
