# backend/bookings/serializers.py
from rest_framework import serializers
from django.db.models import Sum
from .models import Booking
from events.models import Event

class BookingCreateSerializer(serializers.ModelSerializer):
    event = serializers.PrimaryKeyRelatedField(queryset=Event.objects.filter(is_cancelled=False))
    seats = serializers.IntegerField(min_value=1)

    class Meta:
        model = Booking
        fields = ["id", "event", "seats", "amount_cents", "status", "created_at"]
        read_only_fields = ["id", "amount_cents", "status", "created_at"]

    def validate(self, attrs):
        event = attrs["event"]
        seats = attrs["seats"]

        # places déjà prises (pending + confirmed)
        taken = (
            Booking.objects.filter(event=event, status__in=["pending", "confirmed"])
            .aggregate(s=Sum("seats"))["s"] or 0
        )
        available = max(event.max_seats - taken, 0)
        if seats > available:
            raise serializers.ValidationError(
                {"seats": f"Places disponibles: {available}, demandé: {seats}"}
            )
        return attrs

    def create(self, validated_data):
        user = self.context["request"].user
        event = validated_data["event"]
        seats = validated_data["seats"]
        amount = (event.price_cents or 0) * seats
        return Booking.objects.create(
            user=user,
            event=event,
            seats=seats,
            amount_cents=amount,
            status="pending",
        )

class BookingSerializer(serializers.ModelSerializer):
    event_id = serializers.IntegerField(source="event.id", read_only=True)
    event_title = serializers.CharField(source="event.title", read_only=True)
    event_datetime = serializers.DateTimeField(source="event.datetime_start", read_only=True)
    event_city = serializers.CharField(source="event.city", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id", "status", "seats", "amount_cents", "created_at",
            "event_id", "event_title", "event_datetime", "event_city",
        ]
        read_only_fields = fields
