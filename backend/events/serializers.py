# backend/events/serializers.py
from rest_framework import serializers
from .models import Event
from languages.models import Language

class EventSerializer(serializers.ModelSerializer):
    language = serializers.SlugRelatedField(read_only=True, slug_field="code")
    class Meta:
        model = Event
        fields = (
            "id","title","language","venue_name","city","address",
            "datetime_start","max_seats","price_cents","is_cancelled",
        )
        read_only_fields = ("id","is_cancelled")

class EventWriteSerializer(serializers.ModelSerializer):
    language = serializers.SlugRelatedField(queryset=Language.objects.all(), slug_field="code")
    class Meta:
        model = Event
        fields = ["title","language","venue_name","city","address",
                  "datetime_start","max_seats","price_cents"]
