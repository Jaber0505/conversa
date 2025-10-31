"""Partner venue API views."""
from rest_framework import viewsets
from drf_spectacular.utils import (
    extend_schema, extend_schema_view, OpenApiResponse, OpenApiExample
)
from .models import Partner
from .serializers import PartnerSerializer
from common.permissions import IsAuthenticatedAndActive, IsAdminUser


@extend_schema_view(
    list=extend_schema(
        summary="List partner venues",
        description="List all active partner venues that host language exchange events",
        responses={
            200: PartnerSerializer,
            401: OpenApiResponse(description="Unauthenticated"),
        },
        examples=[
            OpenApiExample(
                "Response example",
                value=[
                    {
                        "id": 1,
                        "name": "Bar du Centre",
                        "address": "Rue Exemple 12, Bruxelles",
                        "city": "Brussels",
                        "reputation": 4.5,
                        "capacity": 50,
                        "is_active": True,
                        "created_at": "2025-08-16T19:45:00Z",
                        "updated_at": "2025-08-16T19:45:00Z",
                        "links": {
                            "self": "https://api.conversa.com/api/v1/partners/1/",
                            "events": "https://api.conversa.com/api/v1/events/?partner=1"
                        }
                    }
                ],
                response_only=True,
            )
        ],
    ),
    retrieve=extend_schema(
        summary="Get partner venue details",
        description="Get details of a specific active partner venue",
        responses={
            200: PartnerSerializer,
            404: OpenApiResponse(description="Partner not found")
        },
    ),
    create=extend_schema(
        summary="Create partner venue",
        description="Create a new partner venue (admin only)",
        request=PartnerSerializer,
        responses={201: PartnerSerializer},
        examples=[
            OpenApiExample(
                "Request example",
                value={
                    "name": "Nouvelle Brasserie",
                    "address": "Boulevard Exemple 45, Bruxelles",
                    "city": "Brussels",
                    "reputation": 4.2,
                    "capacity": 80,
                    "is_active": True
                },
                request_only=True,
            )
        ],
    ),
    update=extend_schema(
        summary="Update partner venue (PUT)",
        description="Update an existing partner venue - replaces entire object (admin only)",
        request=PartnerSerializer,
        responses={200: PartnerSerializer},
    ),
    partial_update=extend_schema(
        summary="Partially update partner venue (PATCH)",
        description="Partially update a partner venue - only provided fields are updated (admin only)",
        request=PartnerSerializer,
        responses={200: PartnerSerializer},
    ),
    destroy=extend_schema(
        summary="Delete partner venue",
        description="Delete a partner venue (admin only)",
        responses={204: OpenApiResponse(description="Successfully deleted")},
    ),
)
@extend_schema(tags=["Partners"])
class PartnerViewSet(viewsets.ModelViewSet):
    """
    Partner venue ViewSet.

    Provides CRUD operations for partner venues that host language exchange events.

    Permissions:
        - List/Retrieve: All authenticated users
        - Create/Update/Delete: Admin users only (is_staff or is_superuser)

    Queryset filtering:
        - GET operations (list/retrieve): Only active partners
        - Other operations (create/update/delete): All partners
    """

    serializer_class = PartnerSerializer
    permission_classes = [IsAuthenticatedAndActive]

    def get_permissions(self):
        """Apply admin-only permissions for modification actions."""
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAdminUser()]
        return [IsAuthenticatedAndActive()]

    def get_queryset(self):
        """Filter queryset based on action."""
        # GET (list/retrieve) → only active partners
        if self.action in ["list", "retrieve"]:
            return Partner.objects.filter(is_active=True)
        # Other actions → all partners (for admin operations)
        return Partner.objects.all()
