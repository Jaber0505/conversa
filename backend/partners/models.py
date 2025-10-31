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

        Optimized to avoid N+1 queries using prefetch_related.

        Args:
            datetime_start: Start datetime of the time slot
            datetime_end: End datetime of the time slot (must be 1h after start)

        Returns:
            int: Number of available seats during this time slot

        Note:
            Events are exactly 1 hour long. This method checks all overlapping
            events and calculates remaining capacity.

        Example:
            >>> partner = Partner.objects.get(id=1)
            >>> partner.capacity  # 50 seats
            >>> # 5 events from 18:00-19:00 (6 people each = 30 seats used)
            >>> partner.get_available_capacity('2025-10-10 18:00', '2025-10-10 19:00')
            20  # 50 - 30 = 20 available
        """
        from django.db.models import Prefetch
        from events.models import Event
        from bookings.models import Booking, BookingStatus
        from common.constants import DEFAULT_EVENT_DURATION_HOURS

        # Get all potentially overlapping events at this partner
        # Use prefetch_related to avoid N+1 queries on bookings
        potential_events = Event.objects.filter(
            partner=self,
            status__in=['PUBLISHED', 'AWAITING_PAYMENT']  # Only count active events
        ).prefetch_related(
            Prefetch(
                'bookings',
                queryset=Booking.objects.filter(status=BookingStatus.CONFIRMED),
                to_attr='confirmed_bookings'
            )
        )

        # Filter to only truly overlapping events and count bookings
        total_reserved = 0
        for event in potential_events:
            event_end = event.datetime_start + timedelta(hours=DEFAULT_EVENT_DURATION_HOURS)
            # Check if event overlaps with requested time slot
            if event.datetime_start < datetime_end and event_end > datetime_start:
                # Use prefetched confirmed_bookings (no additional query)
                confirmed_count = len(event.confirmed_bookings)
                total_reserved += confirmed_count

        return max(0, self.capacity - total_reserved)

    def __str__(self):
        status = "[active]" if self.is_active else "[inactive]"
        return f"{self.name} ({self.capacity} seats, {status})"
