"""
Event business logic service.

Handles event creation, validation, and lifecycle management.

ARCHITECTURE RULE:
This service is the SINGLE SOURCE OF TRUTH for all event business logic.
ALL business rules, validations, and state transitions MUST be here.

Business Rules:
- A1: Capacity = 6 participants max (organizer included)
- A2: Max 3 draft events per organizer
- A3: Strict status transitions with validation
- Timezone: Europe/Brussels strict
- 3h advance notice for all critical actions
- Auto-cancellation 1h before start if < 3 participants
"""

from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError

from common.services.base import BaseService
from common.exceptions import EventAlreadyCancelledError
from common.constants import (
    MIN_PARTICIPANTS_PER_EVENT as MIN_PARTICIPANTS,
    MAX_PARTICIPANTS_PER_EVENT as MAX_PARTICIPANTS,
    AUTO_CANCEL_CHECK_HOURS as AUTO_CANCEL_THRESHOLD_HOURS,
    CANCELLATION_DEADLINE_HOURS,
)
from audit.services import AuditService
from ..validators import (
    validate_event_datetime,
    validate_partner_capacity,
)


# Timezone
# Django's timezone utilities use settings.TIME_ZONE ('Europe/Brussels')


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

        # Validate datetime (3h advance, max 7 days future, 12h-21h)
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

        # Mark event as cancelled (validations handled in model/service transition)
        event.mark_cancelled()

        # Cascade cancel all non-cancelled bookings using BookingService
        # to ensure proper refund processing for CONFIRMED bookings
        from bookings.services import BookingService
        bookings_to_cancel = event.bookings.exclude(status=BookingStatus.CANCELLED)
        for booking in bookings_to_cancel:
            try:
                # For manual cancellation, 3h rule is already enforced at event level
                # so we can call the standard cancellation (no system_cancellation)
                BookingService.cancel_booking(
                    booking=booking,
                    cancelled_by=cancelled_by,
                    system_cancellation=False,
                )
            except Exception as e:
                # Log but continue cancelling the rest
                AuditService.log_error(
                    action="cancel_booking_failed",
                    message=f"Failed to cancel booking {booking.public_id} for event {event.id}: {str(e)}",
                    user=cancelled_by,
                    error_details={
                        "booking_id": booking.id,
                        "event_id": event.id,
                        "error": str(e),
                    },
                )
                # Ensure booking is at least marked cancelled even if refund failed
                try:
                    booking.mark_cancelled()
                except Exception:
                    pass

        # Audit log: event cancelled
        AuditService.log_event_cancelled(event, cancelled_by, reason="Manual cancellation")

        return event

    @staticmethod
    def cleanup_expired_drafts():
        """
        Delete DRAFT events whose datetime_start has passed.

        This prevents old drafts from cluttering the database and
        ensures organizers cannot publish events in the past.

        Returns:
            int: Number of drafts deleted
        """
        from events.models import Event

        now = timezone.now()

        # Find all DRAFT events whose start time has passed
        expired_drafts = Event.objects.filter(
            status=Event.Status.DRAFT,
            datetime_start__lt=now
        )

        count = expired_drafts.count()

        # Hard delete these drafts (they were never published)
        expired_drafts.delete()

        return count

    @staticmethod
    def auto_finish_completed_events():
        """
        Automatically mark PUBLISHED events as FINISHED if:
        - Event started more than 1 hour ago (event duration exceeded)

        Also force-completes any ACTIVE games for these events (timeout).

        Returns:
            int: Number of events marked as FINISHED
        """
        from events.models import Event
        from games.models import Game, GameStatus

        now = timezone.now()

        # Events that should be finished (started > 1h ago and still PUBLISHED)
        events_to_finish = Event.objects.filter(
            status=Event.Status.PUBLISHED,
            datetime_start__lt=now - timedelta(hours=1)  # 1h after event start
        ).select_related('organizer')

        finished_count = 0

        for event in events_to_finish:
            # Check if event has an active game that needs to be force-completed
            active_game = Game.objects.filter(
                event=event,
                status=GameStatus.ACTIVE
            ).first()

            if active_game:
                # Force-complete the game (timeout after 1h)
                active_game.status = GameStatus.COMPLETED
                active_game.completed_at = now
                active_game.save(update_fields=['status', 'completed_at', 'updated_at'])

                # Calculate and save final results even if game wasn't finished normally
                from games.services import GameService
                try:
                    GameService._calculate_final_results(active_game)
                except Exception:
                    # If result calculation fails, continue anyway
                    pass

            # Mark event as finished
            event.mark_finished()
            finished_count += 1

        return finished_count

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
                # Cancel event (system cancellation bypasses 3h rule)
                event.mark_cancelled(system_cancellation=True)

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

    # ==========================================================================
    # BUSINESS RULE A1: CAPACITY VALIDATION
    # ==========================================================================

    @staticmethod
    def get_total_participants(event):
        """
        Calculate total participants count (SINGLE SOURCE OF TRUTH).

        Business Rule:
            Total participants = organizer (1) + confirmed bookings

        Args:
            event: Event instance

        Returns:
            int: Total participant count
        """
        from bookings.models import Booking, BookingStatus

        # Organizer always counts as 1 participant
        organizer_count = 1

        # Add confirmed bookings (paid participants)
        confirmed_bookings = Booking.objects.filter(
            event=event,
            status=BookingStatus.CONFIRMED
        ).count()

        return organizer_count + confirmed_bookings

    @staticmethod
    def get_available_slots(event):
        """
        Get number of available booking slots.

        Business Rule:
            Available slots = MAX_PARTICIPANTS - total confirmed participants

        Args:
            event: Event instance

        Returns:
            int: Number of available booking slots
        """
        total_participants = EventService.get_total_participants(event)
        return max(0, MAX_PARTICIPANTS_PER_EVENT - total_participants)


    # ==========================================================================
    # BUSINESS RULE A2: DRAFT LIMIT VALIDATION
    # ==========================================================================

    @staticmethod
    def validate_draft_limit(organizer):
        """
        Validate organizer has not exceeded draft limit.

        Business Rule A2:
            Organizers cannot have more than 3 DRAFT events simultaneously.
            PUBLISHED, PENDING_CONFIRMATION, and CANCELLED events don't count.

        Args:
            organizer: User creating the event

        Raises:
            DRFValidationError: If draft limit exceeded
        """
        from events.models import Event

        draft_count = Event.objects.filter(
            organizer=organizer,
            status=Event.Status.DRAFT
        ).count()

        if draft_count >= 3:
            raise DRFValidationError({
                "error": "Limite de 3 événements en préparation atteinte.",
                "draft_count": draft_count
            })

    # ==========================================================================
    # BUSINESS RULE A3: STATUS TRANSITIONS (STATE MACHINE)
    # ==========================================================================

    @staticmethod
    def get_hours_until_event(event):
        """
        Calculate hours until event start (timezone-safe).

        Ensures datetime comparisons are performed with timezone-aware datetimes
        to avoid TypeError on naive vs aware subtraction.

        Args:
            event: Event instance

        Returns:
            float: Hours until event start
        """
        now = timezone.now()
        event_dt = getattr(event, "datetime_start", None)
        if event_dt is None:
            return -9999.0

        # Make event_dt timezone-aware if naive
        try:
            from django.utils.timezone import is_naive, make_aware, get_current_timezone
            if is_naive(event_dt):
                event_dt = make_aware(event_dt, get_current_timezone())
        except Exception:
            # Fallback: best-effort comparison (may still raise elsewhere)
            pass

        return (event_dt - now).total_seconds() / 3600

    @staticmethod
    def can_perform_action(event, required_hours=3):
        """
        Check if action can be performed based on time until event.

        Business Rule:
            Critical actions require minimum advance notice (default 3h).

        Args:
            event: Event instance
            required_hours: Minimum hours required before event

        Returns:
            tuple: (bool: can_perform, float: hours_until_event)
        """
        hours_until = EventService.get_hours_until_event(event)
        return hours_until >= required_hours, hours_until

    @staticmethod
    @transaction.atomic
    def transition_to_pending_confirmation(event):
        """
        Transition event from DRAFT to PENDING_CONFIRMATION.

        Business Rule A3:
            - Can only transition from DRAFT status
            -             - Must be ≥3h before event start

        Args:
            event: Event instance

        Raises:
            DjangoValidationError: If transition validation fails
        """
        from events.models import Event

        # Validate current status
        if event.status != Event.Status.DRAFT:
            raise DjangoValidationError(
                f"Cannot transition to PENDING_CONFIRMATION from {event.status}. "
                "Only DRAFT events can request publication."
            )

        # Validate 3h advance notice
        can_perform, hours_until = EventService.can_perform_action(event, required_hours=3)
        if not can_perform:
            raise DjangoValidationError(
                f"Cannot publish event: only {hours_until:.1f}h before start "
                "(minimum 3h advance notice required)."
            )

        # Perform transition
        event.status = Event.Status.PENDING_CONFIRMATION
        event.save(update_fields=["status", "updated_at"])

    @staticmethod
    @transaction.atomic
    def transition_to_published(event, published_by=None):
        """
        Transition event from PENDING_CONFIRMATION to PUBLISHED.

        Business Rule A3:
            - Can only transition from PENDING_CONFIRMATION status
            - Payment must be confirmed (validated by webhook)

        Args:
            event: Event instance
            published_by: User who triggered publication (usually organizer)

        Raises:
            DjangoValidationError: If transition validation fails
        """
        from events.models import Event

        # Validate current status
        if event.status != Event.Status.PENDING_CONFIRMATION:
            raise DjangoValidationError(
                f"Cannot mark as PUBLISHED from {event.status}. "
                "Event must be in PENDING_CONFIRMATION status (payment confirmation required)."
            )

        # Perform transition
        now = timezone.now()
        event.status = Event.Status.PUBLISHED
        event.published_at = now
        event.organizer_paid_at = now
        event.save(update_fields=["status", "published_at", "organizer_paid_at", "updated_at"])

        # Ensure organizer has a confirmed booking after publication
        from bookings.models import Booking, BookingStatus

        organizer = event.organizer
        organizer_booking = (
            Booking.objects.filter(user=organizer, event=event)
            .order_by("-created_at")
            .first()
        )

        if organizer_booking:
            if organizer_booking.status != BookingStatus.CONFIRMED:
                organizer_booking.mark_confirmed()
        else:
            # Create and immediately confirm organizer's booking
            new_booking = Booking.objects.create(
                user=organizer,
                event=event,
                amount_cents=event.price_cents,
                is_organizer_booking=True,
            )
            new_booking.mark_confirmed()

        # Audit log
        AuditService.log_event_published(event, published_by or event.organizer)

    @staticmethod
    @transaction.atomic
    def transition_to_cancelled(event, cancelled_by=None, system_cancellation=False):
        """
        Transition event to CANCELLED status.

        Business Rule A3:
            - PUBLISHED events: Can only cancel if Ã¢â€°Â¥3h before start (unless system cancellation)
            - DRAFT/PENDING: Can cancel anytime
            - Cannot cancel if already cancelled

        Args:
            event: Event instance
            cancelled_by: User requesting cancellation (None for system)
            system_cancellation: If True, bypass 3h deadline (auto-cancel)

        Raises:
            DjangoValidationError: If cancellation validation fails
        """
        from events.models import Event

        # Check if already cancelled
        if event.status == Event.Status.CANCELLED:
            raise EventAlreadyCancelledError()

        # Validate 3h notice for PUBLISHED events (unless system cancellation)
        if event.status == Event.Status.PUBLISHED and not system_cancellation:
            can_cancel, hours_until = EventService.can_perform_action(event, required_hours=3)
            if not can_cancel:
                raise DjangoValidationError(
                    f"Cannot cancel PUBLISHED event: only {hours_until:.1f}h before start "
                    "(minimum 3h cancellation notice required)."
                )

        # Perform transition
        event.status = Event.Status.CANCELLED
        event.cancelled_at = timezone.now()
        event.save(update_fields=["status", "cancelled_at", "updated_at"])

    # ==========================================================================
    # PUBLICATION WORKFLOW
    # ==========================================================================

    @staticmethod
    @transaction.atomic
    def request_publication(event, organizer, stripe_module):
        """
        Organizer requests to publish event by creating PaymentIntent.

        Business Rules:
            - Must be organizer
            - Event must be DRAFT
            - Threshold must be reached (Ã¢â€°Â¥3 registrations)
            - Event must be Ã¢â€°Â¥3h in future

        Workflow:
            1. Validate can_request_publication
            2. Create organizer booking (PENDING)
            3. Create Stripe PaymentIntent
            4. Transition to PENDING_CONFIRMATION
            5. After webhook: transition to PUBLISHED

        Args:
            event: Event instance
            organizer: User requesting publication
            stripe_module: Stripe module (injected for testing)

        Returns:
            dict: {
                'client_secret': str,
                'booking_id': str,
                'amount_cents': int
            }

        Raises:
            DRFValidationError: If validation fails
            stripe.error.StripeError: If payment creation fails
        """
        from bookings.models import Booking
        from django.conf import settings

        # Validate permission
        if event.organizer != organizer:
            raise DRFValidationError(
                {"error": "Only organizer can publish event."},
                code='permission_denied'
            )

        # Validate draft status and 3h advance
        if event.status != event.Status.DRAFT:
            raise DRFValidationError({"error": "Event must be in DRAFT status to publish."})
        can_perform, hours_until = EventService.can_perform_action(event, required_hours=3)
        if not can_perform:
            raise DRFValidationError({
                "error": (
                    f"Cannot publish event: only {hours_until:.1f}h before start (minimum 3h advance notice required)."
                )
            })

        # Create organizer booking (PENDING)
        booking = Booking.objects.create(
            user=organizer,
            event=event,
            amount_cents=event.price_cents,
            is_organizer_booking=True
        )

        # Create Stripe PaymentIntent
        stripe_module.api_key = settings.STRIPE_SECRET_KEY

        try:
            payment_intent = stripe_module.PaymentIntent.create(
                amount=event.price_cents,
                currency='eur',
                metadata={
                    'booking_id': str(booking.public_id),
                    'event_id': event.id,
                    'type': 'organizer_publication'
                }
            )

            # Transition to PENDING_CONFIRMATION
            EventService.transition_to_pending_confirmation(event)

            return {
                'client_secret': payment_intent.client_secret,
                'booking_id': str(booking.public_id),
                'amount_cents': event.price_cents
            }

        except stripe_module.error.StripeError as e:
            # Delete booking if Stripe fails
            booking.delete()
            raise
