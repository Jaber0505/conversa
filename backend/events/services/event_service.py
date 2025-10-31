"""
Event business logic service.

Handles event creation, validation, and lifecycle management.
"""

from datetime import timedelta
from django.db import transaction
from django.utils import timezone

from common.services.base import BaseService
from common.exceptions import EventAlreadyCancelledError
from common.constants import (
    MIN_PARTICIPANTS_PER_EVENT as MIN_PARTICIPANTS,
    AUTO_CANCEL_CHECK_HOURS as AUTO_CANCEL_THRESHOLD_HOURS,
)
from audit.services import AuditService
from ..validators import (
    validate_event_datetime,
    validate_partner_capacity,
)


class EventService(BaseService):
    """Service layer for Event business logic."""

    @staticmethod
    @transaction.atomic
    def create_event_with_organizer_booking(organizer, event_data):
        """
        Create event and automatically create booking for organizer.

        This is the main entry point for event creation. It ensures:
        1. Event is created in DRAFT status
        2. Organizer gets a PENDING booking automatically
        3. All validations are performed

        Args:
            organizer: User creating the event
            event_data: Validated event data (from serializer)

        Returns:
            tuple: (Event instance, Booking instance)

        Raises:
            ValidationError: If validations fail
        """
        from events.models import Event
        from bookings.services import BookingService

        # Validate datetime (24h advance, max 7 days future, 12h-21h)
        validate_event_datetime(event_data.get("datetime_start"))

        # Validate partner capacity for this time slot (must have >= 3 available)
        validate_partner_capacity(
            partner=event_data.get("partner"),
            datetime_start=event_data.get("datetime_start")
        )

        # Create event in DRAFT status
        event = Event.objects.create(
            organizer=organizer,
            status=Event.Status.DRAFT,
            **event_data
        )

        # Create organizer's booking
        booking = BookingService.create_booking(
            user=organizer,
            event=event,
            amount_cents=event.price_cents
        )

        # Audit log: event created
        AuditService.log_event_created(event, organizer)

        return event, booking

    @staticmethod
    @transaction.atomic
    def cancel_event(event, cancelled_by):
        """
        Cancel event and cascade to all bookings.

        Args:
            event: Event to cancel
            cancelled_by: User requesting cancellation

        Raises:
            EventAlreadyCancelledError: If event already cancelled
            PermissionError: If user not authorized
        """
        from events.models import Event
        from bookings.models import BookingStatus

        # Check if already cancelled
        if event.status == Event.Status.CANCELLED:
            raise EventAlreadyCancelledError()

        # Verify permissions
        if not event.can_cancel(cancelled_by):
            raise PermissionError("User not authorized to cancel this event.")

        # Mark event as cancelled
        event.mark_cancelled()

        # Cascade cancel all non-cancelled bookings
        now = timezone.now()
        event.bookings.exclude(status=BookingStatus.CANCELLED).update(
            status=BookingStatus.CANCELLED,
            cancelled_at=now,
            updated_at=now
        )

        # Audit log: event cancelled
        AuditService.log_event_cancelled(event, cancelled_by, reason="Manual cancellation")

        return event

    @staticmethod
    def check_and_cancel_underpopulated_events():
        """
        Check for events starting soon with insufficient participants.

        Automatically cancels events that:
        - Are scheduled to start within AUTO_CANCEL_THRESHOLD_HOURS
        - Have fewer than MIN_PARTICIPANTS confirmed bookings
        - Are in PUBLISHED status

        Returns:
            list: Cancelled events
        """
        from events.models import Event
        from bookings.models import BookingStatus

        threshold_time = timezone.now() + timedelta(hours=AUTO_CANCEL_THRESHOLD_HOURS)
        now = timezone.now()

        upcoming_events = Event.objects.filter(
            status=Event.Status.PUBLISHED,
            datetime_start__lte=threshold_time,
            datetime_start__gte=now
        ).select_related('organizer').prefetch_related('bookings')

        cancelled_events = []

        for event in upcoming_events:
            confirmed_count = event.bookings.filter(
                status=BookingStatus.CONFIRMED
            ).count()

            if confirmed_count < MIN_PARTICIPANTS:
                # Cancel event
                event.mark_cancelled()

                # Cancel all non-cancelled bookings WITH refunds
                # Import here to avoid circular dependency
                from bookings.services import BookingService

                bookings_to_cancel = event.bookings.exclude(status=BookingStatus.CANCELLED)
                for booking in bookings_to_cancel:
                    try:
                        # Use service to handle refunds automatically
                        # system_cancellation=True bypasses 3h deadline (event auto-cancelled)
                        BookingService.cancel_booking(
                            booking=booking,
                            cancelled_by=None,  # System action
                            system_cancellation=True  # Bypass deadline check
                        )
                    except Exception as e:
                        # Log but don't stop auto-cancel process
                        AuditService.log_error(
                            action="auto_cancel_booking_failed",
                            message=f"Failed to cancel booking {booking.public_id} during event auto-cancel: {str(e)}",
                            user=booking.user,
                            error_details={
                                "booking_id": booking.id,
                                "event_id": event.id,
                                "error": str(e)
                            }
                        )

                # Audit log: auto-cancelled due to insufficient participants
                AuditService.log_event_cancelled(
                    event,
                    cancelled_by=None,  # System action
                    reason=f"Auto-cancelled: Only {confirmed_count}/{MIN_PARTICIPANTS} participants"
                )

                cancelled_events.append(event)

        return cancelled_events

    @staticmethod
    def get_available_events_for_user(user=None):
        """
        Get list of available events for user.

        Args:
            user: User requesting events (None for anonymous)

        Returns:
            QuerySet: Filtered events
        """
        from events.models import Event

        queryset = Event.objects.select_related(
            'organizer', 'partner', 'language'
        ).all()

        if user and user.is_authenticated:
            # Authenticated users see:
            # - All PUBLISHED events
            # - Their own events (any status)
            from django.db.models import Q
            queryset = queryset.filter(
                Q(status=Event.Status.PUBLISHED) | Q(organizer=user)
            )
        else:
            # Anonymous users only see PUBLISHED events
            queryset = queryset.filter(status=Event.Status.PUBLISHED)

        return queryset.order_by('-datetime_start')

    @staticmethod
    def is_event_full(event):
        """
        Check if event has reached maximum capacity.

        Business Rule:
            Event is full when partner has no more available capacity
            on this time slot (datetime_start to datetime_end).

        Args:
            event: Event instance

        Returns:
            bool: True if full, False otherwise
        """
        # Use event model's is_full property which checks partner capacity
        return event.is_full
