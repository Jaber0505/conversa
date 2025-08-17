from typing import Any, Dict

from django.conf import settings
from django.utils import timezone
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
                "quantity": 1,
                "amount_cents": 700,
                "currency": "EUR",
                "expires_at": "2025-08-17T12:00:00Z",
                "is_expired": False,
                "payment_intent_id": None,
                "confirmed_after_expiry": False,
                "confirmed_at": None,
                "cancelled_at": None,
                "created_at": "2025-08-17T11:45:00Z",
                "updated_at": "2025-08-17T11:45:00Z",
                "links": {
                    "self": "/api/v1/bookings/c1c1c1c1-2b2b-4d4d-9e9e-aaaa1111bbbb/",
                    "event": "/api/v1/events/34/",
                    "cancel": "/api/v1/bookings/c1c1c1c1-2b2b-4d4d-9e9e-aaaa1111bbbb/cancel/",
                    "pay": "/api/v1/payments/create-intent/"
                }
            },
        )
    ]
)
class BookingSerializer(serializers.ModelSerializer):
    is_expired = serializers.SerializerMethodField(help_text="Réservation expirée (TTL dépassé) ?")
    links = serializers.SerializerMethodField(help_text="Liens HATEOAS de la ressource.")

    class Meta:
        model = Booking
        fields = [
            "id", "public_id", "user", "event", "status", "quantity",
            "amount_cents", "currency", "expires_at", "is_expired",
            "payment_intent_id", "confirmed_after_expiry",
            "confirmed_at", "cancelled_at",
            "created_at", "updated_at", "links",
        ]
        read_only_fields = fields
        extra_kwargs = {
            "id": {"help_text": "Identifiant interne numérique."},
            "public_id": {"help_text": "UUID public stable."},
            "user": {"help_text": "Propriétaire de la réservation."},
            "event": {"help_text": "ID de l’évènement réservé."},
            "status": {"help_text": "Statut de la réservation."},
            "quantity": {"help_text": "Nombre de places réservées."},
            "amount_cents": {"help_text": "Montant total en centimes (figé)."},
            "currency": {"help_text": "Devise ISO (ex: EUR)."},
            "expires_at": {"help_text": "Date/heure d’expiration (TTL)."},
            "payment_intent_id": {"help_text": "Stripe PaymentIntent ID."},
            "confirmed_after_expiry": {"help_text": "Paiement confirmé après expiration TTL."},
            "confirmed_at": {"help_text": "Horodatage confirmation."},
            "cancelled_at": {"help_text": "Horodatage annulation."},
            "created_at": {"help_text": "Créé le."},
            "updated_at": {"help_text": "Mis à jour le."},
        }

    def get_is_expired(self, obj: Booking) -> bool:
        return obj.is_expired

    def get_links(self, obj: Booking) -> Dict[str, str]:
        request = self.context.get("request")
        base = "/api/v1"

        def abs_url(path: str) -> str:
            return request.build_absolute_uri(path) if request else path

        ev_ident = getattr(obj.event, "public_id", obj.event_id)
        return {
            "self":   abs_url(f"{base}/bookings/{obj.public_id}/"),
            "event":  abs_url(f"{base}/events/{ev_ident}/"),
            "cancel": abs_url(f"{base}/bookings/{obj.public_id}/cancel/"),
            "pay":    abs_url(f"{base}/payments/create-intent/"),
        }

class BookingCreateSerializer(serializers.Serializer):
    event = serializers.IntegerField(help_text="ID de l’évènement.")
    quantity = serializers.IntegerField(min_value=1, default=1, help_text="Nombre de places (>=1).")

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        from events.models import Event 
        request = self.context["request"]
        user = request.user
        event_id = attrs["event"]
        quantity = int(attrs.get("quantity", 1))

        try:
            event = Event.objects.get(pk=event_id)
        except Event.DoesNotExist:
            raise serializers.ValidationError({"event": ["Évènement introuvable."]})

        if Booking.objects.filter(user=user, event=event, status=BookingStatus.PENDING).exists():
            raise serializers.ValidationError({
                "non_field_errors": ["Vous avez déjà une réservation en attente pour cet évènement."]
            })

        price_cents = int(getattr(event, "price_cents", 0) or 0)
        amount_cents = price_cents * quantity
        currency = getattr(event, "currency", None) or getattr(settings, "DEFAULT_CURRENCY", "EUR")

        attrs["__event"] = event
        attrs["__quantity"] = quantity
        attrs["__amount_cents"] = amount_cents
        attrs["__currency"] = currency
        return attrs

    def create(self, validated_data: Dict[str, Any]) -> Booking:
        request = self.context["request"]
        return Booking.objects.create(
            user=request.user,
            event=validated_data["__event"],
            quantity=validated_data["__quantity"],
            amount_cents=validated_data["__amount_cents"],
            currency=validated_data["__currency"],
        )

    def to_representation(self, instance: Booking) -> Dict[str, Any]:
        return BookingSerializer(instance, context=self.context).data
