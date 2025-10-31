"""Booking serializers for API endpoints."""
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from .models import Booking, BookingStatus


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Booking Example",
            value={
                "id": 12,
                "public_id": "c1c1c1c1-2b2b-4d4d-9e9e-aaaa1111bbbb",
                "user": 5,
                "event": 34,
                "status": "PENDING",
                "amount_cents": 700,
                "currency": "EUR",
                "expires_at": "2025-08-18T20:17:00Z",
                "confirmed_at": None,
                "cancelled_at": None,
                "confirmed_after_expiry": False,
                "created_at": "2025-08-18T20:02:00Z",
                "updated_at": "2025-08-18T20:02:00Z",
                "links": {
                    "self": "/api/v1/bookings/c1c1c1c1-2b2b-4d4d-9e9e-aaaa1111bbbb/",
                    "event": "/api/v1/events/34/",
                    "cancel": "/api/v1/bookings/c1c1c1c1-2b2b-4d4d-9e9e-aaaa1111bbbb/cancel/",
                },
            },
        )
    ]
)
class BookingSerializer(serializers.ModelSerializer):
    """Booking read serializer with HATEOAS links."""

    links = serializers.SerializerMethodField(help_text="HATEOAS links for related resources")

    class Meta:
        model = Booking
        fields = (
            "id",
            "public_id",
            "user",
            "event",
            "status",
            "amount_cents",
            "currency",
            "expires_at",
            "confirmed_at",
            "cancelled_at",
            "confirmed_after_expiry",
            "created_at",
            "updated_at",
            "links",
        )
        read_only_fields = fields

    def get_links(self, obj: Booking) -> dict:
        """Generate HATEOAS links for booking resource."""
        request = self.context.get("request")
        base = request.build_absolute_uri("/")[:-1] if request else ""
        return {
            "self": f"{base}/api/v1/bookings/{obj.public_id}/",
            "event": f"{base}/api/v1/events/{obj.event_id}/",
            "cancel": f"{base}/api/v1/bookings/{obj.public_id}/cancel/",
        }


class BookingCreateSerializer(serializers.Serializer):
    """Booking creation serializer with validation rules."""

    event = serializers.IntegerField(help_text="Event ID to book")

    def validate(self, attrs):
        """
        Validate booking creation.

        Business Rules:
        1. Event must exist
        2. Event must be PUBLISHED (not draft/cancelled)
        3. User cannot have duplicate PENDING booking for same event
        4. Multiple CONFIRMED bookings per event ARE allowed
        """
        # Local import to avoid circular dependency
        from events.models import Event

        request = self.context["request"]
        user = request.user
        event_id = attrs["event"]

        # 1) Check event exists
        try:
            event = Event.objects.get(pk=event_id)
        except Event.DoesNotExist:
            raise serializers.ValidationError({"event": "Event not found."})

        # 2) Event must be PUBLISHED (not draft/awaiting/cancelled)
        if getattr(event, "status", None) != getattr(
            Event.Status, "PUBLISHED", "PUBLISHED"
        ):
            raise serializers.ValidationError(
                "Event is not available for booking."
            )

        # 3) Check for duplicate PENDING booking (user must pay current booking first)
        exists_pending = Booking.objects.filter(
            user=user, event=event, status=BookingStatus.PENDING
        ).exists()
        if exists_pending:
            raise serializers.ValidationError(
                "You already have a pending booking for this event. "
                "Please complete payment before creating a new booking."
            )

        # 4) NOTE: Multiple CONFIRMED bookings ARE ALLOWED
        # User can book multiple seats for the same event

        # Extract pricing from event
        price_cents = int(getattr(event, "price_cents", 0) or 0)
        currency = getattr(event, "currency", "EUR") or "EUR"

        # Store event and pricing in validated data
        attrs["__event"] = event
        attrs["__amount_cents"] = price_cents
        attrs["__currency"] = currency
        return attrs

    def create(self, validated_data):
        """
        Create booking using service layer for proper validation.

        Service layer will validate:
        - Event capacity (>= 3 available slots required)
        """
        from .services import BookingService

        request = self.context["request"]

        # Use service to create booking (validates capacity)
        booking = BookingService.create_booking(
            user=request.user,
            event=validated_data["__event"],
            amount_cents=validated_data["__amount_cents"],
        )
        return booking

    def to_representation(self, instance: Booking):
        """Return booking using read serializer."""
        return BookingSerializer(instance, context=self.context).data
