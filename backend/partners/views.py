"""Partner venue API views."""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import datetime, timedelta
from drf_spectacular.utils import (
    extend_schema, extend_schema_view, OpenApiResponse, OpenApiExample
)
from .models import Partner
from .serializers import PartnerSerializer
from .permissions import IsPartnerOwnerOnly
from common.permissions import IsAuthenticatedAndActive, IsAdminUser


@extend_schema_view(
    list=extend_schema(
        summary="List partner venues",
        description="List all active partner venues that host language exchange events",
        responses={
            200: PartnerSerializer,
            401: OpenApiResponse(description="Unauthenticated"),
        },
        examples=[
            OpenApiExample(
                "Response example",
                value=[
                    {
                        "id": 1,
                        "name": "Bar du Centre",
                        "address": "Rue Exemple 12, Bruxelles",
                        "city": "Brussels",
                        "reputation": 4.5,
                        "capacity": 50,
                        "is_active": True,
                        "created_at": "2025-08-16T19:45:00Z",
                        "updated_at": "2025-08-16T19:45:00Z",
                        "links": {
                            "self": "https://api.conversa.com/api/v1/partners/1/",
                            "events": "https://api.conversa.com/api/v1/events/?partner=1"
                        }
                    }
                ],
                response_only=True,
            )
        ],
    ),
    retrieve=extend_schema(
        summary="Get partner venue details",
        description="Get details of a specific active partner venue",
        responses={
            200: PartnerSerializer,
            404: OpenApiResponse(description="Partner not found")
        },
    ),
    create=extend_schema(
        summary="Create partner venue",
        description="Create a new partner venue (admin only)",
        request=PartnerSerializer,
        responses={201: PartnerSerializer},
        examples=[
            OpenApiExample(
                "Request example",
                value={
                    "name": "Nouvelle Brasserie",
                    "address": "Boulevard Exemple 45, Bruxelles",
                    "city": "Brussels",
                    "reputation": 4.2,
                    "capacity": 80,
                    "is_active": True
                },
                request_only=True,
            )
        ],
    ),
    update=extend_schema(
        summary="Update partner venue (PUT)",
        description="Update an existing partner venue - replaces entire object (admin only)",
        request=PartnerSerializer,
        responses={200: PartnerSerializer},
    ),
    partial_update=extend_schema(
        summary="Partially update partner venue (PATCH)",
        description="Partially update a partner venue - only provided fields are updated (admin only)",
        request=PartnerSerializer,
        responses={200: PartnerSerializer},
    ),
    destroy=extend_schema(
        summary="Delete partner venue",
        description="Delete a partner venue (admin only)",
        responses={204: OpenApiResponse(description="Successfully deleted")},
    ),
)
@extend_schema(tags=["Partners"])
class PartnerViewSet(viewsets.ModelViewSet):
    """
    Partner venue ViewSet.

    Provides CRUD operations for partner venues that host language exchange events.

    Permissions:
        - List/Retrieve: All authenticated users
        - Create/Update/Delete: Admin users only (is_staff or is_superuser)

    Queryset filtering:
        - GET operations (list/retrieve): Only active partners
        - Other operations (create/update/delete): All partners
    """

    serializer_class = PartnerSerializer
    permission_classes = [IsAuthenticatedAndActive]

    def get_permissions(self):
        """
        Apply permissions based on action.

        Business Rules:
            - Regular CRUD (list/retrieve/create/update/destroy): Admin only
            - my_partner: Partner owner ONLY (not admin)
            - my_partner_bookings: Partner owner ONLY (not admin)
        """
        if self.action in ("my_partner", "my_partner_bookings"):
            # Dedicated APIs for partner owner ONLY
            return [IsPartnerOwnerOnly()]
        elif self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAdminUser()]
        return [IsAuthenticatedAndActive()]

    def get_queryset(self):
        """
        Filter queryset based on action.

        Business Rules:
            - list: All active partners (public view)
            - Admin actions: All partners
        """
        # For list action → show all active partners (public view)
        if self.action == "list":
            queryset = Partner.objects.filter(is_active=True)

            # Filter by search query (city, name, or address)
            search = self.request.query_params.get('search', None)
            if search:
                from django.db.models import Q
                queryset = queryset.filter(
                    Q(city__icontains=search) |
                    Q(name__icontains=search) |
                    Q(address__icontains=search)
                )

            return queryset

        # Default: all partners (for admin)
        return Partner.objects.all()

    @extend_schema(
        summary="Get partner availability for a given date",
        description=(
            "Returns hourly slots (12:00..21:00) for the requested date with remaining capacity "
            "for the venue and the max per-event capacity allowed by business rules.\n\n"
            "Rules:\n"
            "- Event duration = 1h\n"
            "- Business hours: start at 12:00..20:59, 21:00 allowed (exact)\n"
            "- Partner capacity respected across overlapping events (sum of max_participants)\n"
            "- New event requires at least 3 seats available; per-event cap is min(6, remaining)\n"
            "- Slots < 3h from now are not creatable"
        ),
        parameters=[],
        responses={200: OpenApiResponse(description="Availability returned")},
    )
    @action(detail=True, methods=["GET"], url_path="availability")
    def availability(self, request, pk=None):
        partner = self.get_object()

        date_str = request.query_params.get("date")
        if not date_str:
            return Response({"error": "Missing 'date' (YYYY-MM-DD)"}, status=status.HTTP_400_BAD_REQUEST)

        # Parse date as naive date, then combine with hours and make aware
        try:
            year, month, day = map(int, date_str.split("-"))
            base_date = datetime(year, month, day)
        except Exception:
            return Response({"error": "Invalid date format. Expected YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        from django.utils.timezone import is_naive, make_aware, get_current_timezone
        tz = get_current_timezone()

        # Build hourly slots: 12:00..21:00
        slots = []
        now = timezone.now()
        from common.constants import (
            DEFAULT_EVENT_DURATION_HOURS,
            MIN_PARTICIPANTS_PER_EVENT as MIN_PAX,
            MAX_PARTICIPANTS_PER_EVENT as MAX_PAX,
            MIN_ADVANCE_BOOKING_HOURS,
        )

        for hour in range(12, 22):  # 12..21 inclusive
            minute = 0
            # Business hours rule: 21:00 allowed only if exactly 21:00
            if hour == 21:
                minute = 0
            elif hour > 21:
                continue

            dt_start = datetime(base_date.year, base_date.month, base_date.day, hour, minute, 0)
            if is_naive(dt_start):
                dt_start = make_aware(dt_start, tz)
            dt_end = dt_start + timedelta(hours=DEFAULT_EVENT_DURATION_HOURS)

            # 3h advance rule
            hours_until = (dt_start - now).total_seconds() / 3600.0

            from partners.services import PartnerService
            remaining = PartnerService.get_available_capacity_by_reservations(
                partner, dt_start, dt_end
            )

            event_cap = min(MAX_PAX, max(0, int(remaining)))
            can_create = (hours_until >= MIN_ADVANCE_BOOKING_HOURS) and (event_cap >= MIN_PAX)

            slots.append(
                {
                    "time": f"{hour:02d}:{minute:02d}",
                    "capacity_remaining": int(remaining),
                    "event_capacity_max": int(event_cap),
                    "can_create": bool(can_create),
                }
            )

        return Response({"date": date_str, "partner": partner.id, "slots": slots}, status=200)

    @extend_schema(
        summary="Get my partner details (owner only)",
        description=(
            "Dedicated API for partner owners to view their partner details.\n\n"
            "Business Rules:\n"
            "- Only accessible to users who own a partner\n"
            "- Admin cannot access this endpoint\n"
            "- Returns the partner they own"
        ),
        responses={
            200: PartnerSerializer,
            403: OpenApiResponse(description="User is not a partner owner"),
        },
    )
    @action(detail=False, methods=["GET", "PATCH"], url_path="my-partner")
    def my_partner(self, request):
        """
        Get or update partner owner's venue.

        Business Rule:
            ONLY users who own a partner can access this endpoint.
            Admin is BLOCKED from this endpoint.

        GET: Returns partner details
        PATCH: Updates partner details

        Returns:
            Response: Partner details
        """
        partner = request.user.owned_partner

        if request.method == "GET":
            serializer = PartnerSerializer(partner, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        elif request.method == "PATCH":
            # Allow partner owner to update their partner
            serializer = PartnerSerializer(
                partner,
                data=request.data,
                partial=True,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Get all bookings for my partner (owner only)",
        description=(
            "Dedicated API for partner owners to view all bookings for events held at their venue.\n\n"
            "Business Rules:\n"
            "- Only accessible to users who own a partner\n"
            "- Admin cannot access this endpoint\n"
            "- Returns all bookings (PENDING, CONFIRMED, CANCELLED) for events at this partner\n"
            "- Ordered by event datetime (most recent first)"
        ),
        responses={
            200: OpenApiResponse(description="List of bookings for this partner"),
            403: OpenApiResponse(description="User is not a partner owner"),
        },
    )
    @action(detail=False, methods=["GET"], url_path="my-partner/bookings")
    def my_partner_bookings(self, request):
        """
        Get all bookings for partner owner's venue.

        Business Rule:
            ONLY users who own a partner can access this endpoint.
            Admin is BLOCKED from this endpoint.
            Returns all bookings for events held at their venue.

        Returns:
            Response: List of bookings with event details
        """
        partner = request.user.owned_partner

        # Get all bookings for events at this partner
        from bookings.models import Booking
        bookings = Booking.objects.filter(
            event__partner=partner
        ).select_related('event', 'user').order_by('-event__datetime_start')

        # Serialize bookings
        from bookings.serializers import BookingSerializer
        serializer = BookingSerializer(bookings, many=True, context={'request': request})

        return Response(serializer.data, status=status.HTTP_200_OK)
