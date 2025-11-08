"""Partner venue models for Conversa."""
import secrets
from datetime import timedelta
from django.db import models


class Partner(models.Model):
    """
    Partner venue model.

    Represents cafes, bars, and venues that host language exchange events.
    Each partner has API key for secure integration and capacity management.
    """

    # Basic information
    name = models.CharField(max_length=255, help_text="Venue name")
    address = models.CharField(max_length=500, help_text="Street address")
    city = models.CharField(
        max_length=100, default="Brussels", help_text="City name"
    )
    reputation = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        default=0.0,
        help_text="Rating out of 5.0",
    )

    # Capacity management
    capacity = models.PositiveIntegerField(
        default=0, help_text="Maximum seats available"
    )
    is_active = models.BooleanField(
        default=True, help_text="Whether venue accepts events"
    )

    # Security
    api_key = models.CharField(
        max_length=64,
        unique=True,
        editable=False,
        help_text="Unique API key for partner integration",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Partner Venue"
        verbose_name_plural = "Partner Venues"

    def save(self, *args, **kwargs):
        """Auto-generate API key on creation."""
        if not self.api_key:
            self.api_key = secrets.token_hex(32)
        super().save(*args, **kwargs)

    def get_available_capacity(self, datetime_start, datetime_end):
        """
        Calculate available capacity for a given time slot.

        ARCHITECTURE RULE:
        This is a lightweight helper that delegates to PartnerService.
        ALL business logic is in PartnerService.get_available_capacity().

        Args:
            datetime_start: Start datetime of the time slot
            datetime_end: End datetime of the time slot (must be 1h after start)

        Returns:
            int: Number of available seats during this time slot

        Example:
            >>> partner = Partner.objects.get(id=1)
            >>> partner.capacity  # 50 seats
            >>> partner.get_available_capacity(datetime_start, datetime_end)
            20  # Available capacity
        """
        from partners.services import PartnerService

        # Delegate to PartnerService (SINGLE SOURCE OF TRUTH)
        return PartnerService.get_available_capacity(
            partner=self,
            datetime_start=datetime_start,
            datetime_end=datetime_end
        )

    def __str__(self):
        status = "[active]" if self.is_active else "[inactive]"
        return f"{self.name} ({self.capacity} seats, {status})"
