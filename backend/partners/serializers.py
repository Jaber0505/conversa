from rest_framework import serializers
from .models import Partner

class PartnerSerializer(serializers.ModelSerializer):
    available_seats = serializers.IntegerField(read_only=True, help_text="Places encore disponibles")
    links = serializers.SerializerMethodField(help_text="Liens HATEOAS")

    class Meta:
        model = Partner
        fields = [
            "id", "name", "address", "reputation",
            "capacity", "available_seats", "is_active",
            "created_at", "updated_at", "links"
        ]
        read_only_fields = ("id", "available_seats", "created_at", "updated_at")

    def get_links(self, obj):
        request = self.context.get("request")
        return {
            "self": request.build_absolute_uri(f"/api/v1/partners/{obj.id}/"),
            "events": request.build_absolute_uri(f"/api/v1/events/?partner={obj.id}")
        }
