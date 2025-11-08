"""
Partner business logic service.

Handles partner venue capacity calculations and business rules.

ARCHITECTURE RULE:
    This service is the SINGLE SOURCE OF TRUTH for all partner business logic.
    Models delegate to this service, views call this service.

BUSINESS RULES:
    - Partners can host multiple simultaneous events
    - Total confirmed bookings cannot exceed venue capacity
    - Capacity is calculated per time slot (considering overlapping events)
    - Minimum 3 seats required to host an event

USAGE EXAMPLE:
    >>> from partners.services import PartnerService
    >>> from partners.models import Partner
    >>> from datetime import datetime
    >>>
    >>> # Check if partner can host event at specific time
    >>> partner = Partner.objects.get(id=1)
    >>> can_host, available, error = PartnerService.can_host_event(
    ...     partner=partner,
    ...     datetime_start=datetime(2025, 10, 10, 18, 0)
    ... )
    >>> if can_host:
    ...     print(f"Partner can host! {available} seats available")
    ... else:
    ...     print(f"Cannot host: {error}")
"""

from datetime import timedelta
from django.db.models import Prefetch

from common.services.base import BaseService
from common.constants import DEFAULT_EVENT_DURATION_HOURS


class PartnerService(BaseService):
    """
    Service layer for Partner business logic.

    This service provides all partner-related business operations:
        - Capacity calculation for time slots
        - Partner search and filtering
        - Event hosting eligibility checks
        - Active partner management

    All methods are @staticmethod for easy testing and no state management.
    """

    @staticmethod
    def get_available_capacity(partner, datetime_start, datetime_end):
        """
        Calculate available capacity for a partner venue at a given time slot.

        This is the CORE capacity calculation method used throughout the application.

        Business Rule:
            Partners can host multiple simultaneous events as long as total
            confirmed bookings don't exceed venue capacity.

            Formula:
                available_capacity = partner.capacity - sum(confirmed_bookings_in_overlapping_events)

        Algorithm:
            1. Find all PUBLISHED/PENDING_CONFIRMATION events at this partner
            2. Filter to only events overlapping with [datetime_start, datetime_end]
            3. Count confirmed bookings in each overlapping event
            4. Return: partner.capacity - total_confirmed_bookings

        Optimization:
            Uses prefetch_related() to avoid N+1 queries when counting bookings.
            Single database query fetches all events with their confirmed bookings.

        Args:
            partner (Partner): Partner instance to check capacity for
            datetime_start (datetime): Start of the time slot (timezone-aware)
            datetime_end (datetime): End of the time slot (must be 1h after start)

        Returns:
            int: Number of available seats during this time slot (>= 0)

        Example:
            >>> from partners.models import Partner
            >>> from partners.services import PartnerService
            >>> from datetime import datetime
            >>> from django.utils import timezone
            >>>
            >>> partner = Partner.objects.get(id=1)
            >>> partner.capacity  # 50 seats
            >>>
            >>> # Scenario: 3 events from 18:00-19:00
            >>> # Event A: 8 confirmed bookings
            >>> # Event B: 12 confirmed bookings
            >>> # Event C: 10 confirmed bookings
            >>> # Total reserved: 30 seats
            >>>
            >>> available = PartnerService.get_available_capacity(
            ...     partner,
            ...     datetime(2025, 10, 10, 18, 0, tzinfo=timezone.utc),
            ...     datetime(2025, 10, 10, 19, 0, tzinfo=timezone.utc)
            ... )
            >>> print(available)
            20  # 50 - 30 = 20 available seats

        Called By:
            - PartnerService.can_host_event()
            - partners.models.Partner.get_available_capacity() (delegate)
            - Event creation validation
        """
        from events.models import Event
        from bookings.models import Booking, BookingStatus

        # Get all potentially overlapping events at this partner
        # Use prefetch_related to avoid N+1 queries on bookings
        potential_events = Event.objects.filter(
            partner=partner,
            status__in=['PUBLISHED', 'PENDING_CONFIRMATION']  # Only count active events
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

        return max(0, partner.capacity - total_reserved)

    @staticmethod
    def get_reserved_capacity_by_events(partner, datetime_start, datetime_end, exclude_event_id=None):
        """
        Calculate reserved capacity based on event capacities (max_participants) for the time slot.

        Business Rule:
            When creating new events, we allocate seats per event (max 6 per event)
            and ensure the sum of allocated seats across overlapping events does not
            exceed the partner's capacity. CANCELLED and FINISHED events do not
            reserve capacity.

        Args:
            partner: Partner instance
            datetime_start: Start of the slot
            datetime_end: End of the slot (1h after start)
            exclude_event_id: Optional event id to exclude from calculation

        Returns:
            int: Total reserved capacity across overlapping events
        """
        from events.models import Event

        active_statuses = [
            Event.Status.DRAFT,
            Event.Status.PENDING_CONFIRMATION,
            Event.Status.PUBLISHED,
        ]

        events = Event.objects.filter(
            partner=partner,
            status__in=active_statuses,
        )
        if exclude_event_id:
            events = events.exclude(id=exclude_event_id)

        total_reserved = 0
        from datetime import timedelta
        from common.constants import DEFAULT_EVENT_DURATION_HOURS
        for ev in events:
            ev_end = ev.datetime_start + timedelta(hours=DEFAULT_EVENT_DURATION_HOURS)
            if ev.datetime_start < datetime_end and ev_end > datetime_start:
                # Reserve per-event capacity (fallback to 6 if not set)
                try:
                    per_event_cap = int(getattr(ev, 'max_participants', 6) or 6)
                except Exception:
                    per_event_cap = 6
                total_reserved += max(0, per_event_cap)

        return total_reserved

    @staticmethod
    def get_available_capacity_by_reservations(partner, datetime_start, datetime_end, exclude_event_id=None):
        """
        Partner available capacity for a time slot considering event-level reservations.

        Returns partner.capacity - sum(max_participants of overlapping active events).
        """
        reserved = PartnerService.get_reserved_capacity_by_events(
            partner, datetime_start, datetime_end, exclude_event_id=exclude_event_id
        )
        return max(0, partner.capacity - reserved)

    @staticmethod
    def search_partners(search_query, active_only=True):
        """
        Search for partners by postal code, city, or name.

        Multi-field search with case-insensitive matching.

        Business Rule:
            Search is case-insensitive and searches across multiple fields:
                - name (e.g., "Café des Arts")
                - postal_code (e.g., "1000")
                - city (e.g., "Brussels")

        Args:
            search_query (str): Search string (can be empty)
            active_only (bool): If True, only return active partners (default: True)

        Returns:
            QuerySet: Filtered partners ordered by name

        Example:
            >>> # Search for partners in Brussels
            >>> partners = PartnerService.search_partners("Brussels")
            >>>
            >>> # Search by postal code
            >>> partners = PartnerService.search_partners("1050")
            >>>
            >>> # Include inactive partners
            >>> all_partners = PartnerService.search_partners("Café", active_only=False)
        """
        from django.db.models import Q
        from partners.models import Partner

        queryset = Partner.objects.all()

        if active_only:
            queryset = queryset.filter(is_active=True)

        if search_query:
            queryset = queryset.filter(
                Q(postal_code__icontains=search_query) |
                Q(city__icontains=search_query) |
                Q(name__icontains=search_query)
            )

        return queryset.order_by('name')

    @staticmethod
    def can_host_event(partner, datetime_start, required_min_capacity=3):
        """
        Check if partner can host an event at specified time.

        Validates partner capacity eligibility for event creation.

        Business Rule:
            Partner must have at least MIN_PARTICIPANTS_PER_EVENT (3)
            available seats at the requested time slot.

            This ensures that even if all participants show up,
            the venue won't be overcrowded.

        Args:
            partner (Partner): Partner instance to check
            datetime_start (datetime): Proposed event start datetime (timezone-aware)
            required_min_capacity (int): Minimum required available seats (default: 3)

        Returns:
            tuple: (can_host, available_capacity, error_message)
                - can_host (bool): True if partner can host the event
                - available_capacity (int): Number of available seats
                - error_message (str or None): Error description if cannot host

        Example:
            >>> from partners.models import Partner
            >>> from datetime import datetime
            >>> from django.utils import timezone
            >>>
            >>> partner = Partner.objects.get(name="Café Central")
            >>> start_time = timezone.now() + timedelta(days=1, hours=18)
            >>>
            >>> can_host, available, error = PartnerService.can_host_event(
            ...     partner=partner,
            ...     datetime_start=start_time,
            ...     required_min_capacity=5  # Need 5 seats minimum
            ... )
            >>>
            >>> if can_host:
            ...     print(f"✓ Can host event! {available} seats available")
            ...     # Proceed with event creation
            ... else:
            ...     print(f"✗ Cannot host: {error}")
            ...     # Show error to user

        Used In:
            - Event creation workflow (validate venue availability)
            - EventService.create_event_with_organizer_booking()
        """
        datetime_end = datetime_start + timedelta(hours=DEFAULT_EVENT_DURATION_HOURS)

        available = PartnerService.get_available_capacity(
            partner,
            datetime_start,
            datetime_end
        )

        if available >= required_min_capacity:
            return True, available, None
        else:
            return False, available, (
                f"Partner '{partner.name}' has insufficient capacity for this time slot. "
                f"Available: {available} seats, Minimum required: {required_min_capacity} seats."
            )

    @staticmethod
    def get_active_partners():
        """
        Get all active partner venues.

        Returns only partners where is_active=True, sorted alphabetically.

        Returns:
            QuerySet: Active partners ordered by name

        Example:
            >>> active_venues = PartnerService.get_active_partners()
            >>> for partner in active_venues:
            ...     print(f"{partner.name} - Capacity: {partner.capacity}")
        """
        from partners.models import Partner
        return Partner.objects.filter(is_active=True).order_by('name')

    @staticmethod
    def is_partner_active(partner):
        """
        Check if partner is currently active.

        Simple helper to check partner.is_active status.

        Args:
            partner (Partner): Partner instance to check

        Returns:
            bool: True if partner is active and accepting events

        Example:
            >>> partner = Partner.objects.get(id=5)
            >>> if PartnerService.is_partner_active(partner):
            ...     print("Partner is accepting new events")
            ... else:
            ...     print("Partner is currently inactive")
        """
        return partner.is_active
