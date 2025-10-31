"""
Booking models for event reservations.

This module defines the Booking model which represents a user's reservation
for a language exchange event.
"""

import uuid
from datetime import timedelta
from django.conf import settings
from django.db import models
from django.db.models import Q, CheckConstraint, UniqueConstraint
from django.utils import timezone


class BookingStatus(models.TextChoices):
    """Booking lifecycle status."""
    PENDING = "PENDING", "Pending"
    CONFIRMED = "CONFIRMED", "Confirmed"
    CANCELLED = "CANCELLED", "Cancelled"


def default_expiry():
    """
    Calculate default expiration time for new bookings.

    Returns:
        datetime: Current time + BOOKING_TTL_MINUTES
    """
    minutes = int(getattr(settings, "BOOKING_TTL_MINUTES", 15))
    return timezone.now() + timedelta(minutes=minutes)


class Booking(models.Model):
    """
    Event booking/reservation model.

    Represents a user's reservation for an event. Bookings have a lifecycle:
    1. PENDING - Created, awaiting payment (expires after 15 minutes)
    2. CONFIRMED - Payment successful, spot reserved
    3. CANCELLED - User cancelled or booking expired

    Business Rules:
    - Each user can have only 1 PENDING booking per event
    - User can have multiple CONFIRMED bookings per event (must pay each separately)
    - PENDING bookings expire after 15 minutes → auto-cancelled
    - CONFIRMED bookings can be cancelled up to 3h before event start
    - User must have paid (CONFIRMED) their current booking before creating a new one
    - Cancelling a booking does not trigger refund (handled externally)
    """

    # Public identifier (UUID for external references)
    public_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
        help_text="Public UUID for external references (Stripe, etc.)"
    )

    # Relationships
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookings",
        help_text="User who made this booking"
    )
    event = models.ForeignKey(
        "events.Event",
        on_delete=models.PROTECT,
        related_name="bookings",
        help_text="Event being booked"
    )

    # Status
    status = models.CharField(
        max_length=16,
        choices=BookingStatus.choices,
        default=BookingStatus.PENDING,
        help_text="Current booking status"
    )

    # Payment details
    amount_cents = models.PositiveIntegerField(
        default=0,
        help_text="Amount paid in cents (e.g., 700 = 7.00€)"
    )
    currency = models.CharField(
        max_length=8,
        default="EUR",
        help_text="Currency code (ISO 4217)"
    )

    # Expiration and payment tracking
    expires_at = models.DateTimeField(
        default=default_expiry,
        help_text="When PENDING booking expires (default 15 minutes)"
    )
    payment_intent_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        help_text="Stripe PaymentIntent ID (for confirmed bookings)"
    )

    # Status timestamps
    confirmed_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When booking was confirmed (payment successful)"
    )
    cancelled_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When booking was cancelled"
    )
    confirmed_after_expiry = models.BooleanField(
        default=False,
        help_text="Whether booking was confirmed after expiration time"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["user", "event"]),
            models.Index(fields=["status"]),
        ]
        constraints = [
            # Amount must be non-negative
            CheckConstraint(
                condition=Q(amount_cents__gte=0),
                name="booking_amount_cents_gte_0"
            ),
            # Only one PENDING booking per user/event
            # (User must pay current booking before creating another)
            UniqueConstraint(
                fields=["user", "event"],
                condition=Q(status=BookingStatus.PENDING),
                name="unique_pending_booking_per_user_event",
            ),
            # NOTE: Multiple CONFIRMED bookings per user/event are ALLOWED
            # User can book multiple seats for the same event
        ]
        verbose_name = "Booking"
        verbose_name_plural = "Bookings"

    def __str__(self) -> str:
        return f"Booking({self.public_id}) {self.user} -> {self.event} [{self.status}]"

    @property
    def is_expired(self) -> bool:
        """
        Check if booking has expired.

        Returns:
            bool: True if PENDING and past expiration time
        """
        return self.status == BookingStatus.PENDING and self.expires_at <= timezone.now()

    def soft_cancel_if_expired(self) -> bool:
        """
        Cancel booking if expired.

        Returns:
            bool: True if booking was expired and cancelled
        """
        if self.is_expired:
            self.mark_cancelled()
            return True
        return False

    def mark_cancelled(self) -> bool:
        """
        Mark booking as cancelled.

        Business Rule:
            Both PENDING and CONFIRMED bookings can be cancelled
            (deadline validation is handled by service layer).

        Returns:
            bool: True if successfully cancelled, False if already cancelled
        """
        if self.status == BookingStatus.CANCELLED:
            return False

        self.status = BookingStatus.CANCELLED
        self.cancelled_at = timezone.now()
        self.save(update_fields=["status", "cancelled_at", "updated_at"])
        return True

    def mark_confirmed(self, payment_intent_id: str | None = None, late: bool = False):
        """
        Mark booking as confirmed after successful payment.

        Args:
            payment_intent_id: Stripe PaymentIntent ID
            late: Whether confirmation happened after expiration
        """
        self.status = BookingStatus.CONFIRMED
        self.confirmed_at = timezone.now()

        if late:
            self.confirmed_after_expiry = True

        if payment_intent_id and not self.payment_intent_id:
            self.payment_intent_id = payment_intent_id

        self.save(update_fields=[
            "status",
            "confirmed_at",
            "confirmed_after_expiry",
            "payment_intent_id",
            "updated_at",
        ])
