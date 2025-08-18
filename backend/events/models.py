from django.conf import settings
from django.db import models
from django.utils import timezone


class Event(models.Model):
    class Difficulty(models.TextChoices):
        EASY = "easy", "Débutant"
        MEDIUM = "medium", "Intermédiaire"
        HARD = "hard", "Avancé"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Brouillon"
        AWAITING_PAYMENT = "AWAITING_PAYMENT", "Paiement en cours"
        PUBLISHED = "PUBLISHED", "Publié"
        CANCELLED = "CANCELLED", "Annulé"

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

    price_cents = models.PositiveIntegerField(default=700, editable=False)

    photo = models.ImageField(upload_to="events/", null=True, blank=True)

    title = models.CharField(max_length=160, editable=False, blank=True, default="")
    address = models.CharField(max_length=255, editable=False, blank=True, default="")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True)
    published_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-datetime_start"]
        indexes = [
            models.Index(fields=["status", "datetime_start"]),
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
        self.title = getattr(self.partner, "name", "") or ""
        self.address = self._partner_address_str()
        self.price_cents = 700
        super().save(*args, **kwargs)

    def can_cancel(self, user) -> bool:
        return bool(user and (user.is_staff or user.id == self.organizer_id)) and self.status != self.Status.CANCELLED

    def mark_published(self):
        if self.status != self.Status.PUBLISHED:
            self.status = self.Status.PUBLISHED
            self.published_at = timezone.now()
            self.save(update_fields=["status", "published_at", "updated_at"])

    def mark_cancelled(self):
        if self.status != self.Status.CANCELLED:
            self.status = self.Status.CANCELLED
            self.cancelled_at = timezone.now()
            self.save(update_fields=["status", "cancelled_at", "updated_at"])

    def __str__(self):
        return f"[{self.id}] {self.title} – {self.datetime_start:%Y-%m-%d %H:%M}"
