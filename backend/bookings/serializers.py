from rest_framework import serializers
from django.utils import timezone
from .models import Booking

class BookingSerializer(serializers.ModelSerializer):
    event_start = serializers.DateTimeField(source="event.datetime_start", read_only=True)
    status = serializers.CharField(read_only=True)

    class Meta:
        model = Booking
        fields = ["id", "event", "user", "status", "event_start", "created_at", "updated_at"]
        read_only_fields = ["id", "user", "status", "event_start", "created_at", "updated_at"]

    def validate(self, data):
        request = self.context["request"]
        event = data["event"]
        now = timezone.now()

        # Éligibilité
        is_cancelled = getattr(event, "is_cancelled", False)
        if not is_cancelled and hasattr(event, "status"):
            is_cancelled = (event.status == "cancelled")
        if is_cancelled:
            raise serializers.ValidationError("Événement annulé.")

        if not event.partner.is_active:
            raise serializers.ValidationError("Partenaire inactif.")

        if now >= event.datetime_start:
            raise serializers.ValidationError("Événement déjà commencé ou passé.")

        # Capacité
        confirmed = event.bookings.filter(status="confirmed").count()
        if confirmed >= event.max_seats:
            raise serializers.ValidationError("Événement complet.")

        # Unicité côté API (en plus de la contrainte DB)
        if event.bookings.filter(user=request.user).exclude(status="cancelled_user").exists():
            raise serializers.ValidationError("Réservation déjà existante pour cet événement.")

        return data

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        booking = Booking(**validated_data)
        booking.full_clean()
        booking.save()
        return booking
