"""
Event models for language exchange events.

This module defines the Event model which represents a language practice session
organized at a partner venue.
"""

from django.conf import settings
from django.core import validators
from django.db import models
from django.utils import timezone

from common.constants import DEFAULT_EVENT_PRICE_CENTS
from .validators import validate_event_datetime


class Event(models.Model):
    """
    Language exchange event model.

    An event represents a scheduled language practice session at a partner venue.
    Each event has an organizer (who pays to create it) and can have up to
    MAX_PARTICIPANTS confirmed participants.

    Business Rules:
    - Organizer must pay when creating event (auto-creates PENDING booking)
    - Max 6 participants (including organizer)
    - Min 3 participants or event auto-cancels 1h before start
    - Fixed price: 7.00ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ per participant
    - Events must be created at least 3h in advance
    """

    class Difficulty(models.TextChoices):
        """Language difficulty levels."""
        EASY = "easy", "Beginner"
        MEDIUM = "medium", "Intermediate"
        HARD = "hard", "Advanced"

    class Status(models.TextChoices):
        """Event lifecycle status."""
        DRAFT = "DRAFT", "Draft"
        PENDING_CONFIRMATION = "PENDING_CONFIRMATION", "Pending Confirmation"
        PUBLISHED = "PUBLISHED", "Published"
        CANCELLED = "CANCELLED", "Cancelled"
        FINISHED = "FINISHED", "Finished"  # NEW

    # Relationships
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organized_events",
        help_text="User who created and organized this event",
    )
    partner = models.ForeignKey(
        "partners.Partner",
        on_delete=models.PROTECT,
        related_name="events",
        help_text="Venue where event takes place",
    )
    language = models.ForeignKey(
        "languages.Language",
        on_delete=models.PROTECT,
        related_name="events",
        help_text="Primary language practiced at this event",
    )

    # Event details
    theme = models.CharField(
        max_length=120,
        help_text="Event theme or topic (e.g., 'French Culture', 'Business English')"
    )
    difficulty = models.CharField(
        max_length=10,
        choices=Difficulty.choices,
        validators=[
            validators.MaxLengthValidator(
                10,
                message="Difficulty must be 10 characters or less"
            )
        ],
        help_text="Difficulty level for this event (max 10 chars)"
    )
    datetime_start = models.DateTimeField(
        validators=[validate_event_datetime],
        help_text="Event start date and time (must be at least 3h in future)"
    )

    # Pricing
    price_cents = models.PositiveIntegerField(
        default=DEFAULT_EVENT_PRICE_CENTS,
        editable=False,
        help_text="Price per participant in cents (7.00ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ = 700 cents)"
    )

    # Participant limits (NEW)
    min_participants = models.PositiveIntegerField(
        default=3,
        help_text="Minimum participants required to confirm event"
    )
    max_participants = models.PositiveIntegerField(
        default=6,
        help_text="Maximum participants (capacity)"
    )

    # Draft visibility (NEW)
    is_draft_visible = models.BooleanField(
        default=True,
        help_text="Deprecated: drafts are private (organizer/admin only)"
    )

    # Organizer payment tracking (NEW)
    organizer_paid_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When organizer paid to publish event"
    )

    # Optional media
    photo = models.ImageField(
        upload_to="events/",
        null=True,
        blank=True,
        help_text="Event cover photo"
    )

    # Game configuration (simplified: only game type, uses event language and difficulty)
    game_type = models.CharField(
        max_length=32,
        null=True,
        blank=True,
        help_text="Pre-configured game type (e.g., 'picture_description', 'word_association'). Uses event's language and difficulty."
    )
    game_started = models.BooleanField(
        default=False,
        help_text="Whether the game has been started by the organizer"
    )

    # Computed fields (auto-generated from partner data)
    title = models.CharField(
        max_length=160,
        editable=False,
        blank=True,
        default="",
        help_text="Auto-generated from partner name"
    )
    address = models.CharField(
        max_length=255,
        editable=False,
        blank=True,
        default="",
        help_text="Auto-generated from partner address"
    )

    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
        help_text="Current event status"
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When event was published (after payment)"
    )
    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When event was cancelled"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-datetime_start"]
        indexes = [
            models.Index(fields=["status", "datetime_start"]),
            models.Index(fields=["partner", "datetime_start"]),
            models.Index(fields=["language", "datetime_start"]),
        ]
        verbose_name = "Event"
        verbose_name_plural = "Events"

    def _partner_address_str(self):
        """Build full address string from partner data."""
        p = self.partner
        # Partner.address already contains the complete address
        return getattr(p, "address", "")

    def save(self, *args, **kwargs):
        """
        Auto-populate computed fields before saving.

        Note: price_cents is enforced as constant, cannot be changed.
        """
        self.title = getattr(self.partner, "name", "") or ""
        self.address = self._partner_address_str()
        self.price_cents = DEFAULT_EVENT_PRICE_CENTS  # Enforce constant price
        super().save(*args, **kwargs)

    def can_cancel(self, user) -> bool:
        """
        Check if user is authorized to cancel this event.

        Args:
            user: User requesting cancellation

        Returns:
            bool: True if user can cancel (organizer or staff)
        """
        return bool(
            user and (user.is_staff or user.id == self.organizer_id)
        ) and self.status != self.Status.CANCELLED

    def mark_published(self, published_by=None):
        """
        Mark event as published (after organizer payment).

        Args:
            published_by: User who triggered publication (usually organizer via payment)
        """
        if self.status != self.Status.PUBLISHED:
            self.status = self.Status.PUBLISHED
            self.published_at = timezone.now()
            self.save(update_fields=["status", "published_at", "updated_at"])

            # Audit log: event published
            from audit.services import AuditService
            AuditService.log_event_published(self, published_by or self.organizer)

    def mark_cancelled(self, cancelled_by=None, system_cancellation=False):
        """
        Mark event as cancelled.

        ARCHITECTURE RULE:
        This is a lightweight helper that delegates to EventService.
        ALL business logic is in EventService.transition_to_cancelled().

        Args:
            cancelled_by: User requesting cancellation (None for system)
            system_cancellation: If True, bypass 3h deadline (auto-cancel)
        """
        from events.services import EventService

        # Delegate to EventService (SINGLE SOURCE OF TRUTH)
        EventService.transition_to_cancelled(
            event=self,
            cancelled_by=cancelled_by,
            system_cancellation=system_cancellation
        )

    @property
    def participants_count(self):
        """
        Get count of confirmed participants only.

        Returns:
            int: Number of confirmed bookings
        """
        from bookings.models import BookingStatus
        return self.bookings.filter(status=BookingStatus.CONFIRMED).count()

    @property
    def booked_seats(self):
        """
        Get count of seats taken (confirmed bookings only).

        Returns:
            int: Number of confirmed bookings consuming a seat
        """
        from bookings.models import BookingStatus
        return self.bookings.filter(status=BookingStatus.CONFIRMED).count()

    @property
    def is_full(self):
        """
        Check if event has reached maximum capacity.

        Business Rule:
            Event is full when partner has no more available capacity
            on this time slot (datetime_start to datetime_end).

        Returns:
            bool: True if partner capacity exhausted
        """
        # Respect per-event max participants first
        if self.max_participants:
            if self.booked_seats >= self.max_participants:
                return True

        available = self.partner.get_available_capacity(
            self.datetime_start,
            self.datetime_end
        )
        return available == 0

    @property
    def available_slots(self):
        """
        Get number of available slots remaining.

        Business Rule:
            Returns partner's available capacity for this time slot.
            This is dynamic and depends on other events at same partner.

        Returns:
            int: Number of slots available on partner at this time
        """
        return self.partner.get_available_capacity(
            self.datetime_start,
            self.datetime_end
        )

    @property
    def datetime_end(self):
        """
        Calculate event end datetime.

        Business Rule:
            All events last exactly 1 hour (DEFAULT_EVENT_DURATION_HOURS).
            This property provides a consistent way to get the end time
            without duplicating the duration calculation everywhere.

        Returns:
            datetime: Event end time (start + duration)
        """
        from datetime import timedelta
        from common.constants import DEFAULT_EVENT_DURATION_HOURS
        return self.datetime_start + timedelta(hours=DEFAULT_EVENT_DURATION_HOURS)


    @property
    def can_request_publication(self) -> bool:
        """
        Check if organizer can request publication.

        Business Rules:
        - Event must be in DRAFT status
        - Event must be >= 3h in future (MIN_ADVANCE_BOOKING_HOURS)
        - Event datetime must not have passed

        Returns:
            bool: True if all conditions met
        """
        from datetime import timedelta
        from common.constants import MIN_ADVANCE_BOOKING_HOURS

        now = timezone.now()
        min_advance = now + timedelta(hours=MIN_ADVANCE_BOOKING_HOURS)

        return (
            self.status == self.Status.DRAFT and
            self.datetime_start >= min_advance and
            self.datetime_start > now  # Event must not have started
        )

    def mark_pending_confirmation(self):
        """
        Mark event as PENDING_CONFIRMATION (organizer payment pending).

        ARCHITECTURE RULE:
        This is a lightweight helper that delegates to EventService.
        ALL business logic is in EventService.transition_to_pending_confirmation().
        """
        from events.services import EventService

        # Delegate to EventService (SINGLE SOURCE OF TRUTH)
        EventService.transition_to_pending_confirmation(event=self)

    def mark_published_by_organizer(self):
        """
        Mark event as PUBLISHED after organizer payment.

        This is called by webhook after organizer pays.

        ARCHITECTURE RULE:
        This is a lightweight helper that delegates to EventService.
        ALL business logic is in EventService.transition_to_published().
        """
        from events.services import EventService

        # Delegate to EventService (SINGLE SOURCE OF TRUTH)
        EventService.transition_to_published(event=self, published_by=self.organizer)

    def mark_finished(self):
        """Mark event as FINISHED (after datetime_start passed)."""
        if self.status != self.Status.FINISHED:
            self.status = self.Status.FINISHED
            self.save(update_fields=["status", "updated_at"])

    def __str__(self):
        return f"[{self.id}] {self.title} -> {self.datetime_start:%Y-%m-%d %H:%M}"
