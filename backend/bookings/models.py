import uuid
from datetime import timedelta
from django.conf import settings
from django.db import models
from django.db.models import Q, CheckConstraint, UniqueConstraint
from django.utils import timezone


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
    amount_cents = models.PositiveIntegerField(default=0)
    currency = models.CharField(max_length=8, default="EUR")

    expires_at = models.DateTimeField(default=default_expiry)
    payment_intent_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)

    confirmed_at = models.DateTimeField(blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)
    confirmed_after_expiry = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["user", "event"]),
            models.Index(fields=["status"]),
        ]
        constraints = [
            CheckConstraint(condition=Q(amount_cents__gte=0), name="booking_amount_cents_gte_0"),
            UniqueConstraint(
                fields=["user", "event"],
                condition=Q(status=BookingStatus.PENDING),
                name="unique_pending_booking_per_user_event",
            ),
            UniqueConstraint(
                fields=["user", "event"],
                condition=Q(status=BookingStatus.CONFIRMED),
                name="unique_confirmed_booking_per_user_event",
            ),
        ]

    def __str__(self) -> str:
        return f"Booking({self.public_id}) {self.user} -> {self.event} [{self.status}]"

    @property
    def is_expired(self) -> bool:
        return self.status == BookingStatus.PENDING and self.expires_at <= timezone.now()

    def soft_cancel_if_expired(self) -> bool:
        if self.is_expired:
            self.mark_cancelled()
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
