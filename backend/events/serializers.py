# backend/events/serializers.py
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from languages.models import Language
from .models import Event

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            name="EventCreateExample",
            value={
                "partner": 1,
                "language": "fr",  # code accepté via SlugRelatedField
                "theme": "Conversation autour du café",
                "difficulty": "easy",
                "datetime_start": "2025-09-01T18:00:00Z",
                "price_cents": 700
            },
            request_only=True,   # exemple pour la requête
            response_only=False,
        ),
        OpenApiExample(
            name="EventResponseExample",
            value={
                "id": 123,
                "partner": 1,
                "partner_name": "Café du Sablon",
                "language": "fr",
                "language_code": "fr",
                "theme": "Conversation autour du café",
                "difficulty": "easy",
                "datetime_start": "2025-09-01T18:00:00Z",
                "max_seats": 6,
                "price_cents": 700,
                "status": "pending",
                "photo": None,
                "organizer_id": 2,
                "created_at": "2025-08-10T12:00:00Z",
                "updated_at": "2025-08-10T12:00:00Z"
            },
            request_only=False,
            response_only=True,  # exemple pour la réponse
        ),
    ]
)
class EventSerializer(serializers.ModelSerializer):
    # Écrire/lire via le code langue (fr, en…)
    language = serializers.SlugRelatedField(
        slug_field="code",
        queryset=Language.objects.all(),
        help_text="Code langue (ex: fr, en)"
    )

    partner_name = serializers.CharField(
        source="partner.name", read_only=True, help_text="Nom du partenaire"
    )
    language_code = serializers.CharField(
        source="language.code", read_only=True, help_text="Code langue (ex: fr, en)"
    )
    organizer_id = serializers.IntegerField(
        source="organizer.id", read_only=True, help_text="ID de l’organisateur"
    )

    class Meta:
        model = Event
        fields = [
            "id",
            "partner", "partner_name",
            "language", "language_code",
            "theme", "difficulty",
            "datetime_start",
            "max_seats", "price_cents",
            "status",
            "photo",
            "organizer_id",
            "created_at", "updated_at",
        ]
        read_only_fields = ["status", "organizer_id", "created_at", "updated_at"]

    def validate(self, data):
        """
        - max_seats ≤ 6
        - le partenaire doit avoir assez de capacité (≥ 3)
        - supporte les PATCH partiels (instance existante)
        """
        partner = data.get("partner") or getattr(self.instance, "partner", None)
        max_seats = data.get("max_seats", getattr(self.instance, "max_seats", 6))

        if max_seats > 6:
            raise serializers.ValidationError("Un événement ne peut pas dépasser 6 places.")

        if partner:
            if partner.capacity < 3:
                raise serializers.ValidationError("Le partenaire n’a pas assez de capacité pour accueillir un événement.")
            if max_seats > partner.capacity:
                raise serializers.ValidationError("Capacité de l’événement supérieure à celle du partenaire.")

        return data
