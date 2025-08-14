# backend/events/models.py
from django.db import models
from django.conf import settings

class Event(models.Model):
    language = models.ForeignKey("languages.Language", on_delete=models.PROTECT, related_name="events")
    title = models.CharField(max_length=140)
    venue_name = models.CharField(max_length=140)
    city = models.CharField(max_length=80)
    address = models.CharField(max_length=200)
    datetime_start = models.DateTimeField()
    max_seats = models.PositiveSmallIntegerField(default=6)
    price_cents = models.PositiveIntegerField(default=0)
    organizer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="organized_events")
    is_cancelled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["datetime_start"]
        indexes = [models.Index(fields=["datetime_start"])]

    def __str__(self):
        return f"{self.title} @ {self.city}"
