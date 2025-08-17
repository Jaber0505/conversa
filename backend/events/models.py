from django.conf import settings
from django.db import models


class Event(models.Model):
    class Difficulty(models.TextChoices):
        EASY = "easy", "Débutant"
        MEDIUM = "medium", "Intermédiaire"
        HARD = "hard", "Avancé"

    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organized_events",
    )
    partner = models.ForeignKey(
        "partners.Partner",
        on_delete=models.PROTECT,
        related_name="events",
    )
    language = models.ForeignKey(
        "languages.Language",
        on_delete=models.PROTECT,
        related_name="events",
    )

    theme = models.CharField(max_length=120)
    difficulty = models.CharField(max_length=10, choices=Difficulty.choices)
    datetime_start = models.DateTimeField()

    # Prix fixe: 7 € (en cents)
    price_cents = models.PositiveIntegerField(default=700, editable=False)

    # Photo optionnelle
    photo = models.ImageField(upload_to="events/", null=True, blank=True)

    # Champs dérivés / méta
    title = models.CharField(max_length=160, editable=False, blank=True, default="")
    address = models.CharField(max_length=255, editable=False, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-datetime_start"]
        indexes = [
            models.Index(fields=["partner", "datetime_start"]),
            models.Index(fields=["language", "datetime_start"]),
        ]

    def _partner_address_str(self):
        p = self.partner
        parts = [
            getattr(p, "address", None),
            getattr(p, "postal_code", None),
            getattr(p, "city", None),
            getattr(p, "country", None),
        ]
        return ", ".join([str(x) for x in parts if x])

    def save(self, *args, **kwargs):
        # Title & address dérivés du partner ; prix verrouillé
        self.title = getattr(self.partner, "name", "") or ""
        self.address = self._partner_address_str()
        self.price_cents = 700
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.id}] {self.title} – {self.datetime_start:%Y-%m-%d %H:%M}"
