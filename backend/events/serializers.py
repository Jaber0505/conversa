from rest_framework import serializers
from rest_framework.reverse import reverse
from django.utils import timezone
from .models import Event


class EventSerializer(serializers.ModelSerializer):
    # Lectures pratiques
    partner_name = serializers.CharField(source="partner.name", read_only=True)
    language_code = serializers.CharField(source="language.code", read_only=True)
    organizer_id = serializers.IntegerField(source="organizer.id", read_only=True)

    # Verrous / dérivés
    title = serializers.CharField(read_only=True)
    address = serializers.CharField(read_only=True)
    price_cents = serializers.IntegerField(read_only=True)
    status = serializers.CharField(read_only=True)
    published_at = serializers.DateTimeField(read_only=True)
    cancelled_at = serializers.DateTimeField(read_only=True)
    photo = serializers.ImageField(required=False, allow_null=True)
    _links = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            "id",
            "organizer", "organizer_id",
            "partner", "partner_name",
            "language", "language_code",
            "theme", "difficulty",
            "datetime_start",
            "price_cents",
            "photo",
            "title", "address",
            "status", "published_at", "cancelled_at",
            "created_at", "updated_at",
            "_links",
        ]
        read_only_fields = [
            "id", "organizer", "organizer_id",
            "price_cents", "title", "address",
            "status", "published_at", "cancelled_at",
            "created_at", "updated_at", "_links",
        ]
        extra_kwargs = {
            "partner": {"required": True},
            "language": {"required": True},
            "theme": {"required": True},
            "difficulty": {"required": True},
            "datetime_start": {"required": True},
        }

    def validate(self, attrs):
        theme = attrs.get("theme", getattr(self.instance, "theme", "")).strip()
        if not theme:
            raise serializers.ValidationError({"theme": "Obligatoire (non vide)."})
        dt = attrs.get("datetime_start", getattr(self.instance, "datetime_start", None))
        if dt and dt <= timezone.now():
            raise serializers.ValidationError({"datetime_start": "Doit être dans le futur."})
        return attrs

    def update(self, instance, validated_data):
        # Verrouiller certains champs
        for locked in ("organizer", "price_cents", "title", "address", "status", "published_at", "cancelled_at"):
            validated_data.pop(locked, None)
        return super().update(instance, validated_data)

    def get__links(self, obj):
        request = self.context.get("request")
        links = {
            "self": reverse("event-detail", args=[obj.pk], request=request),
            "list": reverse("event-list", request=request),
            "partner": None,
        }
        try:
            links["partner"] = reverse("partner-detail", args=[obj.partner_id], request=request)
        except Exception:
            pass

        user = getattr(request, "user", None)
        can_edit = bool(user and (getattr(user, "is_staff", False) or user.id == obj.organizer_id))
        if can_edit:
            links["update"] = links["self"]
            links["delete"] = links["self"]
            links["cancel"] = reverse("event-cancel", args=[obj.pk], request=request)
        return links
