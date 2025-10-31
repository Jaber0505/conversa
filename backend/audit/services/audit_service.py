"""
Audit service for logging business logic events.

This service provides high-level methods for logging important business events
across all modules (Auth, Events, Bookings, Payments, Partners, Users).

Usage:
    from audit.services import AuditService

    AuditService.log_event_created(event, user)
    AuditService.log_payment_success(payment, user)
"""
from audit.models import AuditLog


class AuditService:
    """
    Service for creating audit logs for business events.

    All methods are static and handle audit log creation with proper
    categorization, levels, and metadata.
    """

    # ==========================================================================
    # AUTH EVENTS
    # ==========================================================================

    @staticmethod
    def log_auth_login(user, ip=None, user_agent=None):
        """
        Log successful user login.

        Args:
            user: User who logged in
            ip: Client IP address
            user_agent: Browser user agent string
        """
        return AuditLog.objects.create(
            category=AuditLog.Category.AUTH,
            level=AuditLog.Level.INFO,
            action="login_success",
            message=f"User {user.email} logged in successfully",
            user=user,
            ip=ip,
            user_agent=user_agent or "",
            metadata={"email": user.email, "user_id": user.id}
        )

    @staticmethod
    def log_auth_login_failed(email, ip=None, user_agent=None, reason="invalid_credentials"):
        """
        Log failed login attempt.

        Args:
            email: Email attempted
            ip: Client IP address
            user_agent: Browser user agent string
            reason: Reason for failure (invalid_credentials, account_disabled, etc.)
        """
        return AuditLog.objects.create(
            category=AuditLog.Category.AUTH,
            level=AuditLog.Level.WARNING,
            action="login_failed",
            message=f"Failed login attempt for {email}: {reason}",
            user=None,
            ip=ip,
            user_agent=user_agent or "",
            metadata={"email": email, "reason": reason}
        )

    @staticmethod
    def log_auth_logout(user, ip=None):
        """
        Log user logout.

        Args:
            user: User who logged out
            ip: Client IP address
        """
        return AuditLog.objects.create(
            category=AuditLog.Category.AUTH,
            level=AuditLog.Level.INFO,
            action="logout",
            message=f"User {user.email} logged out",
            user=user,
            ip=ip,
            metadata={"email": user.email, "user_id": user.id}
        )

    @staticmethod
    def log_auth_token_refresh(user, ip=None):
        """Log JWT token refresh."""
        return AuditLog.objects.create(
            category=AuditLog.Category.AUTH,
            level=AuditLog.Level.DEBUG,
            action="token_refreshed",
            message=f"User {user.email} refreshed their access token",
            user=user,
            ip=ip,
            metadata={"user_id": user.id}
        )

    # ==========================================================================
    # EVENT EVENTS
    # ==========================================================================

    @staticmethod
    def log_event_created(event, user):
        """
        Log event creation.

        Args:
            event: Created Event instance
            user: User who created the event (organizer)
        """
        return AuditLog.objects.create(
            category=AuditLog.Category.EVENT,
            level=AuditLog.Level.INFO,
            action="event_created",
            message=f"Event '{event.theme}' created at {event.partner.name}",
            user=user,
            resource_type="Event",
            resource_id=event.id,
            metadata={
                "event_id": event.id,
                "theme": event.theme,
                "partner_id": event.partner_id,
                "partner_name": event.partner.name,
                "partner_capacity": event.partner.capacity,
                "language_code": event.language.code,
                "datetime_start": event.datetime_start.isoformat(),
                "price_cents": event.price_cents,
            }
        )

    @staticmethod
    def log_event_published(event, user):
        """Log event publication (after organizer payment)."""
        return AuditLog.objects.create(
            category=AuditLog.Category.EVENT,
            level=AuditLog.Level.INFO,
            action="event_published",
            message=f"Event '{event.theme}' published after organizer payment",
            user=user,
            resource_type="Event",
            resource_id=event.id,
            metadata={
                "event_id": event.id,
                "theme": event.theme,
                "published_at": event.published_at.isoformat() if event.published_at else None,
            }
        )

    @staticmethod
    def log_event_cancelled(event, cancelled_by, reason=None):
        """
        Log event cancellation.

        Args:
            event: Cancelled Event instance
            cancelled_by: User who cancelled (organizer/admin) or None for system actions
            reason: Optional cancellation reason
        """
        # Handle system cancellations (cancelled_by=None)
        if cancelled_by:
            message = f"Event '{event.theme}' cancelled by {cancelled_by.email}"
            cancelled_by_email = cancelled_by.email
        else:
            message = f"Event '{event.theme}' auto-cancelled by system"
            cancelled_by_email = "system"

        if reason:
            message += f": {reason}"

        return AuditLog.objects.create(
            category=AuditLog.Category.EVENT,
            level=AuditLog.Level.WARNING,
            action="event_cancelled",
            message=message,
            user=cancelled_by,  # Can be None for system actions
            resource_type="Event",
            resource_id=event.id,
            metadata={
                "event_id": event.id,
                "theme": event.theme,
                "cancelled_by_email": cancelled_by_email,
                "cancelled_at": event.cancelled_at.isoformat() if event.cancelled_at else None,
                "reason": reason,
            }
        )

    @staticmethod
    def log_event_auto_cancelled(event, reason="insufficient_participants"):
        """Log automatic event cancellation by system."""
        return AuditLog.objects.create(
            category=AuditLog.Category.SYSTEM,
            level=AuditLog.Level.WARNING,
            action="event_auto_cancelled",
            message=f"Event '{event.theme}' auto-cancelled: {reason}",
            user=None,
            resource_type="Event",
            resource_id=event.id,
            metadata={
                "event_id": event.id,
                "theme": event.theme,
                "reason": reason,
                "participants_count": event.participants_count,
            }
        )

    # ==========================================================================
    # BOOKING EVENTS
    # ==========================================================================

    @staticmethod
    def log_booking_created(booking, user):
        """
        Log booking creation.

        Args:
            booking: Created Booking instance
            user: User who created the booking
        """
        return AuditLog.objects.create(
            category=AuditLog.Category.BOOKING,
            level=AuditLog.Level.INFO,
            action="booking_created",
            message=f"Booking created for event '{booking.event.theme}' by {user.email}",
            user=user,
            resource_type="Booking",
            resource_id=booking.id,
            metadata={
                "booking_id": booking.id,
                "event_id": booking.event_id,
                "event_theme": booking.event.theme,
                "amount_cents": booking.amount_cents,
                "status": booking.status,
            }
        )

    @staticmethod
    def log_booking_confirmed(booking, user):
        """Log booking confirmation (after payment)."""
        return AuditLog.objects.create(
            category=AuditLog.Category.BOOKING,
            level=AuditLog.Level.INFO,
            action="booking_confirmed",
            message=f"Booking confirmed for event '{booking.event.theme}'",
            user=user,
            resource_type="Booking",
            resource_id=booking.id,
            metadata={
                "booking_id": booking.id,
                "event_id": booking.event_id,
                "confirmed_at": booking.confirmed_at.isoformat() if hasattr(booking, 'confirmed_at') and booking.confirmed_at else None,
            }
        )

    @staticmethod
    def log_booking_cancelled(booking, cancelled_by, reason=None):
        """
        Log booking cancellation.

        Args:
            booking: Cancelled Booking instance
            cancelled_by: User who cancelled
            reason: Optional cancellation reason
        """
        return AuditLog.objects.create(
            category=AuditLog.Category.BOOKING,
            level=AuditLog.Level.WARNING,
            action="booking_cancelled",
            message=f"Booking cancelled for event '{booking.event.theme}'" + (f": {reason}" if reason else ""),
            user=cancelled_by,
            resource_type="Booking",
            resource_id=booking.id,
            metadata={
                "booking_id": booking.id,
                "event_id": booking.event_id,
                "cancelled_by_email": cancelled_by.email,
                "reason": reason,
            }
        )

    @staticmethod
    def log_booking_expired(booking):
        """Log booking expiration (not paid within TTL)."""
        return AuditLog.objects.create(
            category=AuditLog.Category.SYSTEM,
            level=AuditLog.Level.INFO,
            action="booking_expired",
            message=f"Booking expired for event '{booking.event.theme}' (not paid within TTL)",
            user=booking.user,
            resource_type="Booking",
            resource_id=booking.id,
            metadata={
                "booking_id": booking.id,
                "event_id": booking.event_id,
                "user_email": booking.user.email,
            }
        )

    # ==========================================================================
    # PAYMENT EVENTS
    # ==========================================================================

    @staticmethod
    def log_payment_initiated(payment, user):
        """Log payment initiation."""
        return AuditLog.objects.create(
            category=AuditLog.Category.PAYMENT,
            level=AuditLog.Level.INFO,
            action="payment_initiated",
            message=f"Payment initiated: {payment.amount_cents / 100:.2f}€",
            user=user,
            resource_type="Payment",
            resource_id=payment.id,
            metadata={
                "payment_id": payment.id,
                "amount_cents": payment.amount_cents,
                "currency": payment.currency,
                "booking_id": payment.booking_id if hasattr(payment, 'booking_id') else None,
            }
        )

    @staticmethod
    def log_payment_success(payment, user):
        """Log successful payment."""
        return AuditLog.objects.create(
            category=AuditLog.Category.PAYMENT,
            level=AuditLog.Level.INFO,
            action="payment_success",
            message=f"Payment successful: {payment.amount_cents / 100:.2f}€",
            user=user,
            resource_type="Payment",
            resource_id=payment.id,
            metadata={
                "payment_id": payment.id,
                "amount_cents": payment.amount_cents,
                "currency": payment.currency,
                "stripe_payment_intent_id": getattr(payment, 'stripe_payment_intent_id', None),
            }
        )

    @staticmethod
    def log_payment_failed(payment, user, error_message):
        """Log failed payment."""
        return AuditLog.objects.create(
            category=AuditLog.Category.PAYMENT,
            level=AuditLog.Level.ERROR,
            action="payment_failed",
            message=f"Payment failed: {error_message}",
            user=user,
            resource_type="Payment",
            resource_id=payment.id,
            metadata={
                "payment_id": payment.id,
                "amount_cents": payment.amount_cents,
                "error": error_message,
            }
        )

    @staticmethod
    def log_payment_refunded(payment, refunded_by, reason=None):
        """Log payment refund."""
        return AuditLog.objects.create(
            category=AuditLog.Category.PAYMENT,
            level=AuditLog.Level.WARNING,
            action="payment_refunded",
            message=f"Payment refunded: {payment.amount_cents / 100:.2f}€" + (f": {reason}" if reason else ""),
            user=refunded_by,
            resource_type="Payment",
            resource_id=payment.id,
            metadata={
                "payment_id": payment.id,
                "amount_cents": payment.amount_cents,
                "refunded_by_email": refunded_by.email if refunded_by else None,
                "reason": reason,
            }
        )

    # ==========================================================================
    # PARTNER EVENTS
    # ==========================================================================

    @staticmethod
    def log_partner_created(partner, created_by):
        """Log partner creation (admin action)."""
        return AuditLog.objects.create(
            category=AuditLog.Category.PARTNER,
            level=AuditLog.Level.INFO,
            action="partner_created",
            message=f"Partner '{partner.name}' created by admin",
            user=created_by,
            resource_type="Partner",
            resource_id=partner.id,
            metadata={
                "partner_id": partner.id,
                "partner_name": partner.name,
                "capacity": partner.capacity,
                "city": partner.city,
            }
        )

    @staticmethod
    def log_partner_updated(partner, updated_by, changed_fields=None):
        """Log partner update."""
        return AuditLog.objects.create(
            category=AuditLog.Category.PARTNER,
            level=AuditLog.Level.INFO,
            action="partner_updated",
            message=f"Partner '{partner.name}' updated",
            user=updated_by,
            resource_type="Partner",
            resource_id=partner.id,
            metadata={
                "partner_id": partner.id,
                "partner_name": partner.name,
                "changed_fields": changed_fields or [],
            }
        )

    @staticmethod
    def log_partner_deactivated(partner, deactivated_by, reason=None):
        """Log partner deactivation."""
        return AuditLog.objects.create(
            category=AuditLog.Category.PARTNER,
            level=AuditLog.Level.WARNING,
            action="partner_deactivated",
            message=f"Partner '{partner.name}' deactivated" + (f": {reason}" if reason else ""),
            user=deactivated_by,
            resource_type="Partner",
            resource_id=partner.id,
            metadata={
                "partner_id": partner.id,
                "partner_name": partner.name,
                "reason": reason,
            }
        )

    # ==========================================================================
    # USER EVENTS
    # ==========================================================================

    @staticmethod
    def log_user_registered(user, ip=None):
        """Log new user registration."""
        return AuditLog.objects.create(
            category=AuditLog.Category.USER,
            level=AuditLog.Level.INFO,
            action="user_registered",
            message=f"New user registered: {user.email}",
            user=user,
            ip=ip,
            resource_type="User",
            resource_id=user.id,
            metadata={
                "user_id": user.id,
                "email": user.email,
                "age": user.age,
            }
        )

    @staticmethod
    def log_user_profile_updated(user, updated_by, changed_fields=None):
        """Log user profile update."""
        return AuditLog.objects.create(
            category=AuditLog.Category.USER,
            level=AuditLog.Level.INFO,
            action="user_profile_updated",
            message=f"User profile updated: {user.email}",
            user=updated_by,
            resource_type="User",
            resource_id=user.id,
            metadata={
                "user_id": user.id,
                "email": user.email,
                "changed_fields": changed_fields or [],
                "updated_by_self": updated_by.id == user.id,
            }
        )

    @staticmethod
    def log_user_deactivated(user, deactivated_by, reason=None):
        """Log user deactivation (admin action)."""
        return AuditLog.objects.create(
            category=AuditLog.Category.ADMIN,
            level=AuditLog.Level.WARNING,
            action="user_deactivated",
            message=f"User {user.email} deactivated by admin" + (f": {reason}" if reason else ""),
            user=deactivated_by,
            resource_type="User",
            resource_id=user.id,
            metadata={
                "user_id": user.id,
                "email": user.email,
                "deactivated_by_email": deactivated_by.email,
                "reason": reason,
            }
        )

    # ==========================================================================
    # SYSTEM & ERROR EVENTS
    # ==========================================================================

    @staticmethod
    def log_error(action, message, user=None, error_details=None):
        """
        Log system error.

        Args:
            action: Action that caused the error
            message: Error message
            user: User associated with error (if any)
            error_details: Additional error details (exception, stack trace, etc.)
        """
        return AuditLog.objects.create(
            category=AuditLog.Category.SYSTEM,
            level=AuditLog.Level.ERROR,
            action=action,
            message=message,
            user=user,
            metadata=error_details or {}
        )

    @staticmethod
    def log_critical(action, message, user=None, error_details=None):
        """Log critical system event."""
        return AuditLog.objects.create(
            category=AuditLog.Category.SYSTEM,
            level=AuditLog.Level.CRITICAL,
            action=action,
            message=message,
            user=user,
            metadata=error_details or {}
        )

    # ==========================================================================
    # PAYMENT EVENTS
    # ==========================================================================

    @staticmethod
    def log_payment_created(payment, user):
        """
        Log payment session creation.

        Args:
            payment: Payment instance
            user: User who initiated payment
        """
        return AuditLog.objects.create(
            category=AuditLog.Category.PAYMENT,
            level=AuditLog.Level.INFO,
            action="payment_created",
            message=f"Payment session created for booking {payment.booking.public_id}",
            user=user,
            resource_type="Payment",
            resource_id=payment.id,
            metadata={
                "payment_id": payment.id,
                "booking_id": payment.booking.id,
                "booking_public_id": str(payment.booking.public_id),
                "amount_cents": payment.amount_cents,
                "currency": payment.currency,
                "stripe_session_id": payment.stripe_checkout_session_id,
            }
        )

    @staticmethod
    def log_payment_succeeded(payment, user, is_free=False):
        """
        Log successful payment.

        Args:
            payment: Payment instance
            user: User who made payment
            is_free: Whether this was a zero-amount booking
        """
        message = f"Payment succeeded for booking {payment.booking.public_id}"
        if is_free:
            message += " (free booking)"

        return AuditLog.objects.create(
            category=AuditLog.Category.PAYMENT,
            level=AuditLog.Level.INFO,
            action="payment_succeeded",
            message=message,
            user=user,
            resource_type="Payment",
            resource_id=payment.id,
            metadata={
                "payment_id": payment.id,
                "booking_id": payment.booking.id,
                "booking_public_id": str(payment.booking.public_id),
                "amount_cents": payment.amount_cents,
                "currency": payment.currency,
                "stripe_payment_intent_id": payment.stripe_payment_intent_id,
                "is_free": is_free,
            }
        )

    @staticmethod
    def log_payment_failed(payment, user, reason=None):
        """
        Log failed payment.

        Args:
            payment: Payment instance
            user: User who attempted payment
            reason: Optional failure reason
        """
        message = f"Payment failed for booking {payment.booking.public_id}"
        if reason:
            message += f": {reason}"

        return AuditLog.objects.create(
            category=AuditLog.Category.PAYMENT,
            level=AuditLog.Level.WARNING,
            action="payment_failed",
            message=message,
            user=user,
            resource_type="Payment",
            resource_id=payment.id,
            metadata={
                "payment_id": payment.id,
                "booking_id": payment.booking.id,
                "booking_public_id": str(payment.booking.public_id),
                "amount_cents": payment.amount_cents,
                "currency": payment.currency,
                "stripe_payment_intent_id": payment.stripe_payment_intent_id,
                "reason": reason,
            }
        )

    @staticmethod
    def log_payment_refunded(payment, cancelled_by, amount_cents=None, refund_id=None, reason=None, is_free=False):
        """
        Log payment refund.

        Args:
            payment: Refund payment instance (negative amount)
            cancelled_by: User who cancelled booking
            amount_cents: Original payment amount (positive)
            refund_id: Stripe refund ID
            reason: Refund reason
            is_free: Whether this was a free booking
        """
        message = f"Payment refunded for booking {payment.booking.public_id}"
        if is_free:
            message += " (free booking cancellation)"
        if refund_id:
            message += f" - Stripe refund: {refund_id}"

        return AuditLog.objects.create(
            category=AuditLog.Category.PAYMENT,
            level=AuditLog.Level.INFO,
            action="payment_refunded",
            message=message,
            user=cancelled_by,
            resource_type="Payment",
            resource_id=payment.id,
            metadata={
                "payment_id": payment.id,
                "booking_id": payment.booking.id,
                "booking_public_id": str(payment.booking.public_id),
                "refund_amount_cents": abs(payment.amount_cents),
                "original_amount_cents": amount_cents,
                "currency": payment.currency,
                "stripe_refund_id": refund_id,
                "reason": reason,
                "is_free": is_free,
            }
        )
