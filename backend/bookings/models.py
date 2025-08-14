# backend/bookings/models.py
from django.db import models
from django.conf import settings

class Booking(models.Model):
    STATUS = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("canceled", "Canceled"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="bookings")
    event = models.ForeignKey("events.Event", on_delete=models.PROTECT, related_name="bookings")
    seats = models.PositiveSmallIntegerField(default=1)
    amount_cents = models.PositiveIntegerField()  # prix figé au moment de la résa
    status = models.CharField(max_length=10, choices=STATUS, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["event", "status"]),
            models.Index(fields=["user", "status"]),
        ]

    def __str__(self):
        return f"Booking #{self.id} {self.status} x{self.seats}"

