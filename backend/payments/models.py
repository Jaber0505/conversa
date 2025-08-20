from django.db import models
from django.conf import settings

class Payment(models.Model):
    STATUS = (
        ("pending", "pending"),
        ("succeeded", "succeeded"),
        ("failed", "failed"),
        ("canceled", "canceled"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payments")
    booking = models.ForeignKey("bookings.Booking", on_delete=models.CASCADE, related_name="payments")

    stripe_checkout_session_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    stripe_payment_intent_id  = models.CharField(max_length=255, blank=True, null=True)

    amount_cents = models.IntegerField(default=0)
    currency     = models.CharField(max_length=10, default="EUR")
    status       = models.CharField(max_length=12, choices=STATUS, default="pending")

    raw_event = models.JSONField(blank=True, null=True)  # dernier event Stripe reçu (audit)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["stripe_checkout_session_id"]),
            models.Index(fields=["stripe_payment_intent_id"]),
            models.Index(fields=["user", "booking"]),
        ]

    def __str__(self):
        return f"Payment#{self.id} {self.status} {self.amount_cents}{self.currency}"
