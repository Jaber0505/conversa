"""
API views for event management.

This module provides RESTful endpoints for creating, listing, updating,
and canceling language exchange events.
"""

from django.db.models import Q
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiResponse,
)

from common.permissions import IsAuthenticatedAndActive, IsOrganizerOrAdmin
from common.exceptions import EventAlreadyCancelledError

from .models import Event
from .serializers import EventSerializer, EventDetailSerializer
from .services import EventService


@extend_schema_view(
    list=extend_schema(
        tags=["Events"],
        summary="List events",
        description=(
            "List all published events, plus your own drafts/awaiting payment events.\n\n"
            "**Visibility Rules:**\n"
            "- All users see PUBLISHED events\n"
            "- Organizers see their own events (any status)\n"
            "- Staff see all events\n\n"
            "**Advanced Search:**\n"
            "Authenticated users can filter by partner, language, and order results."
        ),
        parameters=[
            OpenApiParameter(
                name="partner",
                description="Filter by partner ID",
                required=False,
                type=int,
            ),
            OpenApiParameter(
                name="language",
                description="Filter by language code (e.g., 'fr', 'en')",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="ordering",
                description="Order by field (e.g., 'datetime_start', '-datetime_start')",
                required=False,
                type=str,
            ),
        ],
        responses={
            200: EventSerializer,
            401: OpenApiResponse(description="Authentication required"),
        },
    ),
    retrieve=extend_schema(
        tags=["Events"],
        summary="Get event details",
        description="Retrieve details of a specific event (published or your own draft).",
        responses={
            200: EventSerializer,
            401: OpenApiResponse(description="Authentication required"),
            404: OpenApiResponse(description="Event not found"),
        },
    ),
    create=extend_schema(
        tags=["Events"],
        summary="Create event",
        description=(
            "Create a new language exchange event.\n\n"
            "**Automatic Actions:**\n"
            "- Organizer set to current user\n"
            "- Status set to DRAFT\n"
            "- PENDING booking auto-created for organizer\n\n"
            "**Business Rules:**\n"
            "- Event must be scheduled at least 2 hours in advance\n"
            "- Partner venue must have available capacity\n"
            "- No overlapping events at same partner venue\n"
            "- Price fixed at 7.00€ per participant"
        ),
        request=EventSerializer,
        responses={
            201: EventSerializer,
            400: OpenApiResponse(description="Validation error"),
            409: OpenApiResponse(description="Capacity or schedule conflict"),
        },
    ),
    update=extend_schema(
        tags=["Events"],
        summary="Update event",
        description="Update event (organizer or admin only).",
        request=EventSerializer,
        responses={
            200: EventSerializer,
            403: OpenApiResponse(description="Permission denied"),
        },
    ),
    partial_update=extend_schema(
        tags=["Events"],
        summary="Partial update event",
        description="Partially update event (organizer or admin only).",
        request=EventSerializer,
        responses={
            200: EventSerializer,
            403: OpenApiResponse(description="Permission denied"),
        },
    ),
    destroy=extend_schema(
        tags=["Events"],
        summary="Delete event",
        description=(
            "Permanently delete event (organizer or admin only).\n\n"
            "**Warning:** This is a HARD delete. Consider using cancel instead."
        ),
        responses={
            204: OpenApiResponse(description="Event deleted"),
            403: OpenApiResponse(description="Permission denied"),
        },
    ),
)
class EventViewSet(viewsets.ModelViewSet):
    """
    ViewSet for event management.

    Provides CRUD operations for events with built-in:
    - Authentication (JWT required)
    - Permission checks (organizer or admin for updates)
    - Rate limiting (throttling)
    - Filtering and ordering
    """

    queryset = Event.objects.select_related("organizer", "partner", "language").all()
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticatedAndActive]

    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["datetime_start", "created_at"]
    ordering = ["-datetime_start"]

    def get_serializer_class(self):
        """Use detailed serializer for single event retrieval."""
        if self.action == "retrieve":
            return EventDetailSerializer
        return EventSerializer

    def get_permissions(self):
        """Apply stricter permissions for modification actions."""
        if self.action in ("update", "partial_update", "destroy", "cancel"):
            return [IsAuthenticatedAndActive(), IsOrganizerOrAdmin()]
        return [IsAuthenticatedAndActive()]

    def get_queryset(self):
        """
        Filter queryset based on user permissions and query params.

        Visibility:
        - All users: PUBLISHED events
        - Organizers: Own events (any status)
        - Staff: All events
        """
        qs = super().get_queryset()

        # Apply filters from query parameters
        partner_id = self.request.query_params.get("partner")
        lang_code = self.request.query_params.get("language")

        if partner_id:
            qs = qs.filter(partner_id=partner_id)
        if lang_code:
            qs = qs.filter(language__code=lang_code)

        # Apply visibility rules
        user = self.request.user
        if not getattr(user, "is_staff", False):
            qs = qs.filter(Q(status=Event.Status.PUBLISHED) | Q(organizer_id=user.id))

        return qs

    def perform_create(self, serializer):
        """
        Create event and auto-create organizer booking.

        Uses EventService to handle business logic:
        - Validates datetime, partner availability, capacity
        - Creates event in DRAFT status
        - Auto-creates PENDING booking for organizer
        """
        # Use service layer for business logic
        event, booking = EventService.create_event_with_organizer_booking(
            organizer=self.request.user,
            event_data=serializer.validated_data,
        )

        # Assign created event to serializer instance for proper response
        serializer.instance = event

    def get_throttles(self):
        """Apply different rate limits for read vs write operations."""
        self.throttle_scope = (
            "events_read" if self.action in ("list", "retrieve") else "events_write"
        )
        return super().get_throttles()

    @extend_schema(
        tags=["Events"],
        summary="Cancel event",
        description=(
            "Cancel event and all associated bookings.\n\n"
            "**Actions:**\n"
            "- Mark event as CANCELLED\n"
            "- Cancel all bookings (PENDING and CONFIRMED)\n\n"
            "**Permissions:** Organizer or admin only\n\n"
            "**Note:** Refunds must be processed separately"
        ),
        responses={
            200: EventSerializer,
            403: OpenApiResponse(description="Permission denied"),
            409: OpenApiResponse(description="Event already cancelled"),
        },
    )
    @action(detail=True, methods=["POST"], url_path="cancel", url_name="cancel")
    def cancel(self, request, pk=None):
        """Cancel event using EventService."""
        event = self.get_object()  # Permission already checked by IsOrganizerOrAdmin

        try:
            # Use service layer for business logic
            EventService.cancel_event(event=event, cancelled_by=request.user)

            serializer = self.get_serializer(event)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except EventAlreadyCancelledError:
            # Event already cancelled - return current state
            serializer = self.get_serializer(event)
            return Response(serializer.data, status=status.HTTP_200_OK)
