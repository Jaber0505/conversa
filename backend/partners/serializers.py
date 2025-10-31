"""Partner serializers."""
from rest_framework import serializers
from .models import Partner


class PartnerSerializer(serializers.ModelSerializer):
    """
    Partner venue serializer.

    Includes HATEOAS links for API navigation.

    Note:
        available_seats field removed - capacity is time-slot specific,
        use Partner.get_available_capacity(start, end) for accurate availability.
    """

    links = serializers.SerializerMethodField(help_text="HATEOAS navigation links")

    class Meta:
        model = Partner
        fields = [
            "id", "name", "address", "city", "reputation",
            "capacity", "is_active",
            "created_at", "updated_at", "links"
        ]
        read_only_fields = ("id", "created_at", "updated_at")

    def get_links(self, obj):
        """Generate HATEOAS links."""
        request = self.context.get("request")
        if not request:
            return {}

        return {
            "self": request.build_absolute_uri(f"/api/v1/partners/{obj.id}/"),
            "events": request.build_absolute_uri(f"/api/v1/events/?partner={obj.id}")
        }
