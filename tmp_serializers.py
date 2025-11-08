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
            "min_participants", "max_participants",
            "is_draft_visible",
            "organizer_paid_at",
            "created_at", "updated_at",
            "_links",
        ]
        read_only_fields = [
            "id", "organizer", "organizer_id",
            "price_cents", "title", "address",
            "status", "published_at", "cancelled_at",
            "min_participants", "max_participants",
            "is_draft_visible", "organizer_paid_at",
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

        Note: datetime_start validation (â‰¥3h advance, max 7 days, business hours)
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

    # Removed getters for registration fields

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
            # Exposer delete uniquement pour les DRAFT (delete draft)
            if obj.status == obj.Status.DRAFT:
                links["delete_draft"] = links["self"]
            # Annuler l'événement (uniquement si possible)
            try:
                from .services import EventService
                can_cancel, _ = EventService.can_perform_action(obj, required_hours=3)
                if obj.status == obj.Status.PUBLISHED and can_cancel:
                    links["cancel"] = reverse("event-cancel", args=[obj.pk], request=request)
            except Exception:
                pass

            # Pay-and-publish link for organizer (new workflow)
            if obj.can_request_publication:
                try:
                    pay_url = reverse("event-pay-and-publish", args=[obj.pk], request=request)
                    links["pay_and_publish"] = pay_url
                    # Backward compatibility for front expecting this key
                    links["request_publication"] = pay_url
                except Exception:
                    pass

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

    # User-specific booking info and permissions
    my_booking = serializers.SerializerMethodField()
    can_cancel_booking = serializers.SerializerMethodField()
    is_starting_soon = serializers.SerializerMethodField()
    cancellation_deadline_hours = serializers.SerializerMethodField()

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
            # user-scoped
            "my_booking",
            "can_cancel_booking",
            "is_starting_soon",
            "cancellation_deadline_hours",
            "permissions",
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

    # --------------------- User-scoped helpers ---------------------
    def _get_current_user(self):
        request = self.context.get("request")
        return getattr(request, "user", None)

    def get_my_booking(self, obj):
        """Return current user's booking public_id and status for this event, if any."""
        user = self._get_current_user()
        if not user or not getattr(user, "is_authenticated", False):
            return None
        try:
            from bookings.models import Booking
            booking = (
                Booking.objects
                .filter(user_id=user.id, event_id=obj.id)
                .order_by("-created_at")
                .first()
            )
            if not booking:
                return None
            return {"public_id": str(booking.public_id), "status": booking.status}
        except Exception:
            return None

    def get_can_cancel_booking(self, obj):
        user = self._get_current_user()
        if not user or not getattr(user, "is_authenticated", False):
            return False
        try:
            from bookings.models import Booking, BookingStatus
            booking = (
                Booking.objects
                .filter(user_id=user.id, event_id=obj.id)
                .order_by("-created_at")
                .first()
            )
            if not booking or booking.status != BookingStatus.CONFIRMED:
                return False
            from .services import EventService
            can_cancel, _ = EventService.can_perform_action(obj, required_hours=3)
            return can_cancel
        except Exception:
            return False

    def get_is_starting_soon(self, obj):
        try:
            from .services import EventService
            can_cancel, _ = EventService.can_perform_action(obj, required_hours=3)
            return not can_cancel
        except Exception:
            return False

    def get_cancellation_deadline_hours(self, obj):
        try:
            from common.constants import CANCELLATION_DEADLINE_HOURS
            return CANCELLATION_DEADLINE_HOURS
        except Exception:
            return 3

    def get_permissions(self, obj):
        """Expose action permissions to drive UI from server."""
        request = self.context.get("request")
        user = getattr(request, "user", None)
        is_auth = bool(user and getattr(user, "is_authenticated", False))

        perms = {
            "can_request_publication": False,
            "can_cancel_event": False,
            "can_book": False,
            "can_pay_booking": False,
            "can_cancel_booking": False,
            "disable_reason_code": None,
        }

        # Organizer permissions
        is_organizer = bool(user and (getattr(user, "is_staff", False) or getattr(user, "id", None) == getattr(obj, "organizer_id", None)))
        try:
            from .services import EventService
            can_cancel_event_now, _ = EventService.can_perform_action(obj, required_hours=3)
        except Exception:
            can_cancel_event_now = False

        if is_organizer and obj.status == obj.Status.DRAFT and getattr(obj, "can_request_publication", False):
            perms["can_request_publication"] = True

        if is_organizer and obj.status == obj.Status.PUBLISHED and can_cancel_event_now:
            perms["can_cancel_event"] = True
        if obj.status == obj.Status.PUBLISHED and not can_cancel_event_now:
            perms["disable_reason_code"] = "STARTING_SOON"

        # User booking permissions
        if is_auth:
            myb = self.get_my_booking(obj)
            if myb:
                if myb.get("status") == "PENDING":
                    perms["can_pay_booking"] = True
                if myb.get("status") == "CONFIRMED":
                    perms["can_cancel_booking"] = self.get_can_cancel_booking(obj)
            else:
                # can book if published, not cancelled/finished and capacity available
                try:
                    is_published = obj.status == obj.Status.PUBLISHED
                    capacity = getattr(obj, "partner_capacity", None)
                    participants = getattr(obj, "participants_count", 0)
                    not_full = (capacity is None) or (participants < capacity)
                    perms["can_book"] = bool(is_published and not_full)
                except Exception:
                    perms["can_book"] = obj.status == obj.Status.PUBLISHED

        return perms

