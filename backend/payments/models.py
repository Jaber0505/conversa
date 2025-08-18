from django.db import models
from django.conf import settings

class Payment(models.Model):
    STATUS_CHOICES = [
        ("pending", "pending"),
        ("succeeded", "succeeded"),
        ("failed", "failed"),
        ("canceled", "canceled"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payments"
    )
    booking = models.ForeignKey(
        "bookings.Booking", on_delete=models.CASCADE, related_name="payments"
    )

    amount_cents = models.PositiveIntegerField(default=0)
    currency = models.CharField(max_length=10, default="EUR")
    stripe_payment_intent_id = models.CharField(
        max_length=64, blank=True, null=True, db_index=True
    )
    status = models.CharField(
        max_length=12, choices=STATUS_CHOICES, default="pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["stripe_payment_intent_id"]),
            models.Index(fields=["user", "booking"]),
        ]

    def __str__(self):
        return f"Payment({self.id}) {self.status} {self.amount_cents}{self.currency}"
