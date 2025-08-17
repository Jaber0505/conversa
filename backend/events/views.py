from rest_framework import viewsets, filters
from drf_spectacular.utils import (
    extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse
)
from common.permissions import IsAuthenticatedAndActive, IsOrganizerOrAdmin
from .models import Event
from .serializers import EventSerializer


@extend_schema_view(
    list=extend_schema(
        tags=["Events"],
        description="Lister les événements (auth requis)",
        parameters=[
            OpenApiParameter(name="partner", description="Filtrer par ID partenaire", required=False, type=int),
            OpenApiParameter(name="language", description="Filtrer par code langue (ex: fr)", required=False, type=str),
            OpenApiParameter(name="ordering", description="Ex: datetime_start,-datetime_start", required=False, type=str),
        ],
        responses={200: EventSerializer, 401: OpenApiResponse(description="Non authentifié")},
    ),
    retrieve=extend_schema(
        tags=["Events"],
        description="Détail d’un événement (auth requis)",
        responses={200: EventSerializer, 401: OpenApiResponse(description="Non authentifié"), 404: OpenApiResponse(description="Non trouvé")},
    ),
    create=extend_schema(
        tags=["Events"],
        description="Créer un événement (organisateur = user courant). Champs obligatoires: partner, language, datetime_start, theme, difficulty.",
        request=EventSerializer,
        responses={201: EventSerializer, 400: OpenApiResponse(description="Données invalides")},
    ),
    update=extend_schema(
        tags=["Events"],
        description="Mettre à jour un événement (organisateur de l’event ou admin).",
        request=EventSerializer,
        responses={200: EventSerializer, 403: OpenApiResponse(description="Interdit")},
    ),
    partial_update=extend_schema(
        tags=["Events"],
        description="Modifier partiellement un événement (organisateur de l’event ou admin).",
        request=EventSerializer,
        responses={200: EventSerializer, 403: OpenApiResponse(description="Interdit")},
    ),
    destroy=extend_schema(
        tags=["Events"],
        description="Supprimer un événement (organisateur de l’event ou admin). Suppression HARD.",
        responses={204: OpenApiResponse(description="Supprimé")},
    ),
)
class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.select_related("organizer", "partner", "language").all()
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticatedAndActive]

    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["datetime_start", "created_at"]
    ordering = ["-datetime_start"]
    # http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_permissions(self):
        if self.action in ("update", "partial_update", "destroy"):
            return [IsAuthenticatedAndActive(), IsOrganizerOrAdmin()]
        return [IsAuthenticatedAndActive()]

    def get_queryset(self):
        qs = super().get_queryset()
        partner_id = self.request.query_params.get("partner")
        lang_code = self.request.query_params.get("language")
        if partner_id:
            qs = qs.filter(partner_id=partner_id)
        if lang_code:
            qs = qs.filter(language__code=lang_code)
        return qs

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)

    def get_throttles(self):
        self.throttle_scope = "events_read" if self.action in ("list", "retrieve") else "events_write"
        return super().get_throttles()
