from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from .models import Booking, BookingStatus


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Exemple Booking",
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
    links = serializers.SerializerMethodField(help_text="Liens HATEOAS utiles.")

    class Meta:
        model = Booking
        fields = (
            "id", "public_id", "user", "event", "status",
            "amount_cents", "currency",
            "expires_at", "confirmed_at", "cancelled_at", "confirmed_after_expiry",
            "created_at", "updated_at",
            "links",
        )
        read_only_fields = fields

    def get_links(self, obj: Booking) -> dict:
        request = self.context.get("request")
        base = request.build_absolute_uri("/")[:-1] if request else ""
        return {
            "self": f"{base}/api/v1/bookings/{obj.public_id}/",
            "event": f"{base}/api/v1/events/{obj.event_id}/",
            "cancel": f"{base}/api/v1/bookings/{obj.public_id}/cancel/",
        }


class BookingCreateSerializer(serializers.Serializer):
    event = serializers.IntegerField(help_text="ID interne de l’évènement.")

    def validate(self, attrs):
        # import local pour éviter un import circulaire
        from events.models import Event

        request = self.context["request"]
        user = request.user
        event_id = attrs["event"]

        # 1) existence event
        try:
            event = Event.objects.get(pk=event_id)
        except Event.DoesNotExist:
            raise serializers.ValidationError({"event": "Évènement introuvable."})

        # 2) l'évènement doit être PUBLISHED (les brouillons / awaiting / cancelled sont non réservables)
        if getattr(event, "status", None) != getattr(Event.Status, "PUBLISHED", "PUBLISHED"):
            raise serializers.ValidationError("L’évènement n’est pas disponible à la réservation.")

        # 3) règles d’unicité par (user, event)
        exists_pending = Booking.objects.filter(
            user=user, event=event, status=BookingStatus.PENDING
        ).exists()
        if exists_pending:
            raise serializers.ValidationError("Réservation en attente déjà existante pour cet évènement.")

        exists_confirmed = Booking.objects.filter(
            user=user, event=event, status=BookingStatus.CONFIRMED
        ).exists()
        if exists_confirmed:
            raise serializers.ValidationError("Vous avez déjà une réservation confirmée pour cet évènement.")

        price_cents = int(getattr(event, "price_cents", 0) or 0)
        currency = getattr(event, "currency", "EUR") or "EUR"

        attrs["__event"] = event
        attrs["__amount_cents"] = price_cents
        attrs["__currency"] = currency
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        booking = Booking.objects.create(
            user=request.user,
            event=validated_data["__event"],
            amount_cents=validated_data["__amount_cents"],
            currency=validated_data["__currency"],
        )
        return booking

    def to_representation(self, instance: Booking):
        return BookingSerializer(instance, context=self.context).data
