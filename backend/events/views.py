"""
API views for event management.

This module provides RESTful endpoints for creating, listing, updating,
and canceling language exchange events.
"""

from django.db.models import Q
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, APIException
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
            "- Event must be scheduled at least 3 hours in advance\n"
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
        - Participants: For retrieve action, allow accessing events they booked (any status)
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
            # Default visibility for non-staff
            base_filter = Q(status=Event.Status.PUBLISHED) | Q(organizer_id=user.id)

            # For retrieve action, also allow events the user has booked (history needs details
            # for CANCELLED/FINISHED events the user participated in)
            if getattr(self, "action", None) == "retrieve":
                qs = qs.filter(base_filter | Q(bookings__user_id=user.id)).distinct()
            else:
                qs = qs.filter(base_filter)

        return qs

    def destroy(self, request, *args, **kwargs):
        """Safely delete events.

        Business rule:
        - Allow hard delete only for DRAFT events.
        - For DRAFT, proactively delete related bookings (if any) to avoid
          on_delete=PROTECT conflicts, then delete the event.
        - For non‑DRAFT events, guide clients to use the cancel endpoint.
        """
        from django.db import IntegrityError
        event = self.get_object()
        from .models import Event
        if event.status == Event.Status.DRAFT:
            try:
                # Best effort: delete any related bookings before deleting the event
                related = getattr(event, 'bookings', None)
                if related is not None:
                    related.all().delete()
                return super().destroy(request, *args, **kwargs)
            except IntegrityError as e:
                return Response(
                    {
                        "error": "Cannot delete draft event due to linked data.",
                        "code": "conflict",
                    },
                    status=status.HTTP_409_CONFLICT,
                )
        # Non‑draft: prefer cancellation to keep auditability and refunds
        return Response(
            {
                "error": "Cannot hard delete a non-draft event. Use the cancel endpoint.",
                "code": "business_rule_violation",
            },
            status=status.HTTP_409_CONFLICT,
        )

    def perform_create(self, serializer):
        """
        Create event in DRAFT status (NO payment required).

        NEW WORKFLOW:
        - Creates event in DRAFT status
        - Event visible to organizer/admin only)"
        - NO booking created yet (organizer pays later)

        ALL BUSINESS LOGIC delegated to EventService:
        - A2: Draft limit validation (max 3 drafts)
        - Datetime validation
        - Partner capacity validation
        """
        from .validators import validate_event_datetime, validate_partner_capacity
        from common.logging_service import LoggingService

        validated_data = serializer.validated_data

        # Log event creation start
        LoggingService.log_event_creation_start(self.request.user, validated_data)

        try:
            # A2: Validate draft limit using EventService (SINGLE SOURCE OF TRUTH)
            # Patch encoding issue by normalizing message if raised here
            try:
                EventService.validate_draft_limit(self.request.user)
            except ValidationError as e:
                # Log validation error
                LoggingService.log_validation_error(
                    "Draft limit validation failed",
                    category="event",
                    validation_errors={"draft_limit": str(e)},
                    user=self.request.user
                )
                # Normalize French accents in error message for clients
                try:
                    draft_count = None
                    if hasattr(e, "detail") and isinstance(e.detail, dict):
                        draft_count = e.detail.get("draft_count")
                    raise ValidationError({
                        "error": "Limite de 3 événements en préparation atteinte.",
                        "draft_count": draft_count,
                    })
                except Exception:
                    # Fallback: re-raise original if unexpected structure
                    raise e

            # Validate datetime and partner capacity
            try:
                validate_event_datetime(validated_data.get("datetime_start"))
            except ValidationError as e:
                LoggingService.log_validation_error(
                    "Event datetime validation failed",
                    category="event",
                    validation_errors={"datetime": str(e)},
                    user=self.request.user
                )
                raise

            try:
                validate_partner_capacity(
                    partner=validated_data.get("partner"),
                    datetime_start=validated_data.get("datetime_start")
                )
            except ValidationError as e:
                LoggingService.log_validation_error(
                    "Partner capacity validation failed",
                    category="event",
                    validation_errors={"partner_capacity": str(e)},
                    user=self.request.user
                )
                raise

            # Compute allowed per-event capacity based on partner availability for this slot
            from partners.services import PartnerService
            from common.constants import MIN_PARTICIPANTS_PER_EVENT as MIN_PAX, MAX_PARTICIPANTS_PER_EVENT as MAX_PAX

            dt_start = validated_data.get("datetime_start")
            # End based on default duration (validators already enforce exact 1h)
            from datetime import timedelta
            from common.constants import DEFAULT_EVENT_DURATION_HOURS
            dt_end = dt_start + timedelta(hours=DEFAULT_EVENT_DURATION_HOURS)

            available_for_slot = PartnerService.get_available_capacity_by_reservations(
                partner=validated_data.get("partner"),
                datetime_start=dt_start,
                datetime_end=dt_end,
            )

            # Per-event capacity is capped by MAX_PAX (6) and slot availability
            per_event_cap = min(MAX_PAX, max(0, int(available_for_slot)))
            if per_event_cap < MIN_PAX:
                # Safety: should be caught by validate_partner_capacity, but double-check
                error_msg = f"Insufficient capacity to create event (available {available_for_slot}, minimum {MIN_PAX})."
                LoggingService.log_validation_error(
                    error_msg,
                    category="event",
                    validation_errors={"capacity": error_msg},
                    user=self.request.user
                )
                raise ValidationError({"capacity": error_msg})

            # Create event in DRAFT status (no payment) with computed max_participants
            event = Event.objects.create(
                organizer=self.request.user,
                status=Event.Status.DRAFT,
                is_draft_visible=True,
                max_participants=per_event_cap,
                **validated_data
            )

            # Log success
            LoggingService.log_event_creation_success(event, self.request.user)

            # Audit log
            from audit.services import AuditService
            AuditService.log_event_created(event, self.request.user)

            # Assign to serializer
            serializer.instance = event

        except Exception as e:
            # Log any unexpected errors
            if not isinstance(e, ValidationError):
                LoggingService.log_event_creation_error(
                    self.request.user,
                    validated_data,
                    e
                )
            raise

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
            "Actions:\n"
            "- Mark event as CANCELLED\n"
            "- Cancel all bookings (PENDING and CONFIRMED)\n\n"
            "Permissions: Organizer or admin only\n\n"
            "Refunds: Automatic refunds are processed for confirmed bookings"
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
        event = self.get_object()
        try:
            EventService.cancel_event(event=event, cancelled_by=request.user)
            serializer = self.get_serializer(event)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except EventAlreadyCancelledError:
            # Raise a DRF API exception so the global handler formats the envelope
            class Conflict(APIException):
                status_code = status.HTTP_409_CONFLICT
                default_code = "conflict"

            raise Conflict(detail="Event already cancelled")

    @extend_schema(
        tags=["Events"],
        summary="Pay and publish event (organizer only)",
        description=(
            "Organizer pays to publish event - creates booking and Stripe checkout session.\n\n"
            "**Workflow:**\n"
            "1. Validate event is DRAFT\n"
            "2. Create organizer booking (PENDING)\n"
            "3. Create Stripe Checkout Session\n"
            "4. Return Stripe URL for payment\n"
            "5. After webhook: Event → PUBLISHED, Booking → CONFIRMED\n\n"
            "**Business Rules:**\n"
            "- Must be organizer\n"
            "- Event must be DRAFT\n"
            "- Event ≥3h in future"
        ),
        responses={
            200: OpenApiResponse(description="Stripe checkout URL created"),
            400: OpenApiResponse(description="Cannot publish"),
            403: OpenApiResponse(description="Not organizer"),
        },
    )
    @action(detail=True, methods=["POST"], url_path="pay-and-publish", url_name="pay-and-publish")
    def pay_and_publish(self, request, pk=None):
        """
        Create booking and Stripe checkout session for organizer to pay and publish event.

        Simplified flow: DRAFT → pay → PUBLISHED (no intermediate status)
        """
        import re
        from urllib.parse import urlencode
        from django.conf import settings
        from bookings.models import Booking
        from payments.services import PaymentService
        from rest_framework.exceptions import PermissionDenied
        from common.logging_service import LoggingService

        event = self.get_object()

        LoggingService.log_info(
            f"Pay and publish initiated for event {event.id}",
            category="event",
            extra={"event_id": event.id, "user_id": request.user.id}
        )

        try:
            # Validate organizer
            if event.organizer != request.user:
                LoggingService.log_warning(
                    f"Unauthorized publish attempt for event {event.id}",
                    category="event",
                    extra={"event_id": event.id, "user_id": request.user.id}
                )
                raise PermissionDenied("Only organizer can publish event.")

            # Validate event status
            if event.status != Event.Status.DRAFT:
                LoggingService.log_warning(
                    f"Invalid event status for publishing: {event.status}",
                    category="event",
                    extra={"event_id": event.id, "status": event.status}
                )
                raise ValidationError({"error": "Event must be in DRAFT status to publish."})

            # Validate 3h advance
            can_perform, hours_until = EventService.can_perform_action(event, required_hours=3)
            if not can_perform:
                LoggingService.log_warning(
                    f"Event {event.id} publish failed: insufficient advance notice ({hours_until:.1f}h)",
                    category="event",
                    extra={"event_id": event.id, "hours_until": hours_until}
                )
                raise ValidationError({
                    "error": f"Cannot publish event: only {hours_until:.1f}h before start (minimum 3h advance notice required)."
                })

            # Get or create organizer booking (PENDING)
            # Reuse existing PENDING booking if user came back from Stripe without paying
            from bookings.models import BookingStatus
            booking, created = Booking.objects.get_or_create(
                user=request.user,
                event=event,
                status=BookingStatus.PENDING,
                defaults={
                    'amount_cents': event.price_cents,
                    'is_organizer_booking': True
                }
            )

            if created:
                LoggingService.log_booking_creation_success(booking, request.user)

            # Get lang from request
            lang = re.sub(r"[^A-Za-z\-]", "", request.data.get("lang", "fr")).strip() or "fr"

            # Build return URLs
            base = getattr(settings, "FRONTEND_BASE_URL", "http://localhost:4200").rstrip("/")
            success_path = f"/{lang}/stripe/success"
            cancel_path = f"/{lang}/stripe/cancel"

            qs = {"b": str(booking.public_id), "e": str(event.id), "lang": lang}
            success_url = f"{base}{success_path}?{urlencode(qs)}&cs={{CHECKOUT_SESSION_ID}}"
            cancel_url = f"{base}{cancel_path}?{urlencode(qs)}"

            # Log payment creation start
            LoggingService.log_payment_creation_start(booking, request.user)

            # Create Stripe Checkout Session
            try:
                stripe_url, session_id, _payment = PaymentService.create_checkout_session(
                    booking=booking,
                    user=request.user,
                    success_url=success_url,
                    cancel_url=cancel_url,
                )

                LoggingService.log_payment_creation_success(_payment, booking, request.user)

                return Response({
                    "url": stripe_url,
                    "session_id": session_id,
                    "booking_id": str(booking.public_id)
                }, status=status.HTTP_200_OK)

            except ValidationError as e:
                # Delete booking if checkout session creation fails
                LoggingService.log_payment_creation_error(booking, request.user, e)
                booking.delete()
                raise e

        except Exception as e:
            if not isinstance(e, (ValidationError, PermissionDenied)):
                LoggingService.log_error(
                    f"Unexpected error in pay_and_publish for event {event.id}",
                    category="event",
                    exception=e,
                    extra={"event_id": event.id, "user_id": request.user.id},
                    user=request.user
                )
            raise

    @extend_schema(
        tags=["Events"],
        summary="[Legacy] Request publication (alias)",
        description=(
            "Alias rétro-compatibilité. Redirige la logique vers pay-and-publish.\n\n"
            "Fronts anciens peuvent encore appeler /request-publication/."
        ),
        responses={
            200: OpenApiResponse(description="Stripe checkout URL created"),
            400: OpenApiResponse(description="Cannot publish"),
            403: OpenApiResponse(description="Not organizer"),
        },
    )
    @action(detail=True, methods=["POST"], url_path="request-publication", url_name="request-publication")
    def request_publication(self, request, pk=None):
        """Alias pour compat: utilise pay_and_publish sous le capot."""
        return self.pay_and_publish(request, pk)
