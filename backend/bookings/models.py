from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError

class Booking(models.Model):
    STATUS_CHOICES = [
        ("confirmed", "Confirmé"),
        # ("pending", "En attente"),          # activer plus tard si paiement
        ("cancelled_user", "Annulé par l'utilisateur"),
        # ("cancelled_admin", "Annulé admin"), # optionnel
    ]

    event = models.ForeignKey("events.Event", on_delete=models.CASCADE, related_name="bookings")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="confirmed")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event", "user"],
                name="unique_booking_per_user_event",
            ),
        ]
        indexes = [
            models.Index(fields=["event", "status"]),
            models.Index(fields=["user", "status"]),
        ]


    def __str__(self):
        return f"{self.user_id} -> {self.event_id} [{self.status}]"

    def clean(self):
        """
        Garde-fous côté modèle (complétés côté serializer).
        """
        # 1) Event annulé ?
        is_cancelled = getattr(self.event, "is_cancelled", False)
        if not is_cancelled and hasattr(self.event, "status"):
            is_cancelled = (self.event.status == "cancelled")
        if is_cancelled:
            raise ValidationError("Événement annulé.")

        # 2) Event passé ?
        if timezone.now() >= self.event.datetime_start:
            raise ValidationError("Événement déjà commencé ou passé.")

        # 3) Partner actif ?
        if not self.event.partner.is_active:
            raise ValidationError("Partenaire inactif.")

        # 4) Capacité atteinte ?
        confirmed = self.event.bookings.filter(status="confirmed").count()
        if confirmed >= self.event.max_seats:
            raise ValidationError("Événement complet.")
