# backend/payments/models.py
from django.db import models
from django.conf import settings

class Payment(models.Model):
    STATUS = [
        ("pending", "Pending"),
        ("succeeded", "Succeeded"),
        ("failed", "Failed"),
        ("canceled", "Canceled"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="payments")
    booking = models.ForeignKey("bookings.Booking", on_delete=models.PROTECT, related_name="payments")
    amount_cents = models.PositiveIntegerField()
    currency = models.CharField(max_length=10, default=getattr(settings, "STRIPE_CURRENCY", "eur"))

    stripe_payment_intent_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS, default="pending")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"Payment#{self.pk} {self.status} {self.amount_cents}{self.currency}"
