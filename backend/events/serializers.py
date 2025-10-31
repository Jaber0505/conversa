from rest_framework import serializers
from rest_framework.reverse import reverse
from django.utils import timezone
from .models import Event


class EventSerializer(serializers.ModelSerializer):
    # Read-only practical fields
    partner_name = serializers.CharField(source="partner.name", read_only=True)
    partner_city = serializers.CharField(source="partner.city", read_only=True)
    language_code = serializers.CharField(source="language.code", read_only=True)
    organizer_id = serializers.IntegerField(source="organizer.id", read_only=True)

    # Auto-generated / locked fields
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
            "partner", "partner_name", "partner_city",
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
        """
        Validate event data.

        Note: datetime_start validation (24h advance, max 7 days, business hours)
        is handled by model validators and EventService, not here.
        """
        theme = attrs.get("theme", getattr(self.instance, "theme", "")).strip()
        if not theme:
            raise serializers.ValidationError(
                {"theme": "Theme is required and cannot be empty."}
            )
        # datetime_start validation delegated to model validators
        return attrs

    def update(self, instance, validated_data):
        # Lock certain fields from being updated
        locked_fields = (
            "organizer", "price_cents", "title", "address",
            "status", "published_at", "cancelled_at"
        )
        for field in locked_fields:
            validated_data.pop(field, None)
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


class EventDetailSerializer(EventSerializer):
    """
    Extended event serializer for detail view with computed fields.

    Includes additional information that is expensive to compute:
    - participants_count: Number of confirmed bookings for this event
    - available_slots: Available capacity at partner for this time slot
    - is_full: Whether event has reached capacity

    Also exposes additional partner and organizer details.
    """

    # Additional partner information
    partner_address = serializers.CharField(source="partner.address", read_only=True)
    partner_capacity = serializers.IntegerField(source="partner.capacity", read_only=True)

    # Additional language information
    language_name = serializers.CharField(source="language.label_en", read_only=True)

    # Organizer information
    organizer_first_name = serializers.CharField(source="organizer.first_name", read_only=True)
    organizer_last_name = serializers.CharField(source="organizer.last_name", read_only=True)

    # Computed fields from model properties
    participants_count = serializers.SerializerMethodField()
    available_slots = serializers.SerializerMethodField()
    is_full = serializers.SerializerMethodField()

    class Meta(EventSerializer.Meta):
        fields = EventSerializer.Meta.fields + [
            "partner_address",
            "partner_capacity",
            "language_name",
            "organizer_first_name",
            "organizer_last_name",
            "participants_count",
            "available_slots",
            "is_full",
        ]

    def get_participants_count(self, obj):
        """Get count of confirmed participants for this specific event."""
        return obj.participants_count

    def get_available_slots(self, obj):
        """Get available capacity at partner venue for this time slot."""
        return obj.available_slots

    def get_is_full(self, obj):
        """Check if event has reached maximum capacity."""
        return obj.is_full
