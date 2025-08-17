from uuid import UUID
from rest_framework import serializers
from bookings.models import Booking

class CreateIntentSerializer(serializers.Serializer):
    booking_public_id = serializers.CharField(required=False, help_text="UUID public de la réservation (préféré).")
    booking = serializers.IntegerField(required=False, min_value=1, help_text="ID numérique (rétro-compat).")

    def validate(self, attrs):
        if not attrs.get("booking_public_id") and not attrs.get("booking"):
            raise serializers.ValidationError("Fournir booking_public_id (UUID) ou booking (ID).")
        return attrs


class ConfirmIntentSerializer(serializers.Serializer):
    booking_public_id = serializers.CharField(required=False)
    booking = serializers.IntegerField(required=False, min_value=1)
    payment_method = serializers.CharField(required=False, default="pm_card_visa")

    def validate(self, attrs):
        request = self.context["request"]
        ident = attrs.get("booking_public_id") or attrs.get("booking")
        if not ident:
            raise serializers.ValidationError({"booking_public_id": ["Obligatoire (ou 'booking' id)."]})
        try:
            UUID(str(ident))
            booking = Booking.objects.filter(public_id=ident, user=request.user).first()
        except Exception:
            booking = Booking.objects.filter(pk=ident, user=request.user).first()
        if not booking:
            raise serializers.ValidationError({"booking_public_id": ["Réservation introuvable."]})
        attrs["__booking"] = booking
        return attrs
