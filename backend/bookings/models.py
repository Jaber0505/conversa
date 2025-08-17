import uuid
from datetime import timedelta
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.db.models import Q, CheckConstraint, UniqueConstraint


class BookingStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    CONFIRMED = "CONFIRMED", "Confirmed"
    CANCELLED = "CANCELLED", "Cancelled"

def default_expiry():
    minutes = int(getattr(settings, "BOOKING_TTL_MINUTES", 15))
    return timezone.now() + timedelta(minutes=minutes)

class Booking(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings")
    event = models.ForeignKey("events.Event", on_delete=models.PROTECT, related_name="bookings")
    status = models.CharField(max_length=16, choices=BookingStatus.choices, default=BookingStatus.PENDING)
    quantity = models.PositiveSmallIntegerField()
    amount_cents = models.PositiveIntegerField()
    currency = models.CharField(max_length=3, default="EUR")
    expires_at = models.DateTimeField(default=default_expiry)
    payment_intent_id = models.CharField(max_length=128, blank=True, null=True)
    confirmed_after_expiry = models.BooleanField(default=False)
    confirmed_at = models.DateTimeField(blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["public_id"]),
            models.Index(fields=["status"]),
            models.Index(fields=["user", "event"]),
        ]
        constraints = [
            CheckConstraint(condition=Q(quantity__gte=1), name="booking_quantity_gte_1"),
            CheckConstraint(condition=Q(amount_cents__gte=0), name="booking_amount_cents_gte_0"),

            UniqueConstraint(
                fields=["user", "event"],
                condition=Q(status="PENDING"),
                name="unique_pending_booking_per_user_event",
            ),
        ]

    @property
    def is_expired(self) -> bool:
        return self.status == BookingStatus.PENDING and timezone.now() >= self.expires_at

    def soft_cancel_if_expired(self) -> bool:
        if self.is_expired:
            self.status = BookingStatus.CANCELLED
            self.cancelled_at = timezone.now()
            self.save(update_fields=["status", "cancelled_at", "updated_at"])
            return True
        return False

    def mark_cancelled(self) -> bool:
        if self.status == BookingStatus.CONFIRMED:
            return False
        self.status = BookingStatus.CANCELLED
        self.cancelled_at = timezone.now()
        self.save(update_fields=["status", "cancelled_at", "updated_at"])
        return True

    def mark_confirmed(self, payment_intent_id: str | None = None, late: bool = False):
        self.status = BookingStatus.CONFIRMED
        self.confirmed_at = timezone.now()
        if late:
            self.confirmed_after_expiry = True
        if payment_intent_id and not self.payment_intent_id:
            self.payment_intent_id = payment_intent_id
        self.save(update_fields=[
            "status", "confirmed_at", "confirmed_after_expiry", "payment_intent_id", "updated_at"
        ])
