from django.db import models
from django.conf import settings

class Event(models.Model):
    DIFFICULTY_CHOICES = [
        ("easy", "Facile"),
        ("medium", "Moyen"),
        ("hard", "Difficile"),
    ]

    STATUS_CHOICES = [
        ("pending", "En attente"),
        ("finished", "Terminé"),
        ("cancelled", "Annulé"),
        ("full", "Complet"),
    ]

    partner = models.ForeignKey("partners.Partner", on_delete=models.PROTECT, related_name="events")
    language = models.ForeignKey("languages.Language", on_delete=models.PROTECT, related_name="events")
    organizer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="organized_events")

    theme = models.CharField(max_length=200)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    datetime_start = models.DateTimeField()

    max_seats = models.PositiveSmallIntegerField(default=6)
    price_cents = models.PositiveIntegerField(default=700)
    photo = models.ImageField(upload_to="event_photos/", null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["datetime_start"]
        indexes = [
            models.Index(fields=["datetime_start"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.partner.name} - {self.language.code} ({self.theme})"

    # 🔒 logique métier
    def clean(self):
        """
        - max_seats ≤ 6 sauf si le partenaire a moins de sièges restants
        - on ne peut pas créer un event si le partenaire n’a pas assez de places
        """
        partner_capacity = self.partner.capacity
        if self.max_seats > 6:
            self.max_seats = 6
        if self.max_seats > partner_capacity:
            self.max_seats = partner_capacity
        if partner_capacity < 3:
            raise ValueError("Impossible de créer un événement : le partenaire n’a pas assez de capacité.")
