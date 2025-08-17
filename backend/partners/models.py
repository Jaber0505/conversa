import secrets
from django.db import models

class Partner(models.Model):
    name = models.CharField(max_length=255)                       # Nom du bar/café
    address = models.CharField(max_length=500)     
    city = models.CharField(max_length=100, default="Bruxelles")             # Adresse complète
    reputation = models.DecimalField(max_digits=2, decimal_places=1, default=0.0)  # Note sur 5

    capacity = models.PositiveIntegerField(default=0)             # Nb de places max dans ce lieu
    is_active = models.BooleanField(default=True)                 # Si le lieu est ouvert aux events

    api_key = models.CharField(max_length=64, unique=True, editable=False)  # Clé API unique

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.api_key:  # si vide ou null
            import secrets
            self.api_key = secrets.token_hex(32)
        super().save(*args, **kwargs)

    @property
    def available_seats(self):
        """Capacité restante (en tenant compte des events associés)."""
        total_reserved = sum(event.seats_reserved for event in self.events.all())
        return max(self.capacity - total_reserved, 0)

    def __str__(self):
        status = "✅" if self.is_active else "❌"
        return f"{self.name} ({self.capacity} places, {status})"
