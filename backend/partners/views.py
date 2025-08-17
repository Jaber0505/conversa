from rest_framework import viewsets
from drf_spectacular.utils import (
    extend_schema, extend_schema_view, OpenApiResponse, OpenApiExample
)
from .models import Partner
from .serializers import PartnerSerializer
from common.permissions import IsAuthenticatedAndActive

@extend_schema_view(
    list=extend_schema(
        description="Lister tous les partenaires actifs",
        responses={
            200: PartnerSerializer,
            401: OpenApiResponse(description="Non authentifié"),
        },
        examples=[
            OpenApiExample(
                "Exemple de réponse",
                value=[
                    {
                        "id": 1,
                        "name": "Bar du Centre",
                        "address": "Rue Exemple 12, Bruxelles",
                        "reputation": 4.5,
                        "capacity": 50,
                        "available_seats": 30,
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
        description="Détails d’un partenaire actif",
        responses={200: PartnerSerializer, 404: OpenApiResponse(description="Non trouvé")},
    ),
    create=extend_schema(
        description="Créer un nouveau partenaire",
        request=PartnerSerializer,
        responses={201: PartnerSerializer},
        examples=[
            OpenApiExample(
                "Exemple de requête",
                value={
                    "name": "Nouvelle Brasserie",
                    "address": "Boulevard Exemple 45, Bruxelles",
                    "reputation": 4.2,
                    "capacity": 80,
                    "is_active": True
                },
                request_only=True,
            )
        ],
    ),
    update=extend_schema(
        description="Mettre à jour un partenaire existant (remplace tout l’objet)",
        request=PartnerSerializer,
        responses={200: PartnerSerializer},
    ),
    partial_update=extend_schema(
        description="Modifier partiellement un partenaire (PATCH)",
        request=PartnerSerializer,
        responses={200: PartnerSerializer},
    ),
    destroy=extend_schema(
        description="Supprimer un partenaire",
        responses={204: OpenApiResponse(description="Supprimé avec succès")},
    ),
)
@extend_schema(tags=["Partners"])
class PartnerViewSet(viewsets.ModelViewSet):
    serializer_class = PartnerSerializer
    permission_classes = [IsAuthenticatedAndActive]

    def get_queryset(self):
        # GET (list/retrieve) → seulement les partenaires actifs
        if self.action in ["list", "retrieve"]:
            return Partner.objects.filter(is_active=True)
        return Partner.objects.all()
