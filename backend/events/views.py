from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import (
    extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse
)
from common.permissions import IsAuthenticatedAndActive, IsOrganizerOrAdmin
from .models import Event
from .serializers import EventSerializer

# bookings
from bookings.models import Booking, BookingStatus


@extend_schema_view(
    list=extend_schema(
        tags=["Events"],
        description="Lister les événements publiés (et mes brouillons/attente si je suis le créateur).",
        parameters=[
            OpenApiParameter(name="partner", description="Filtrer par ID partenaire", required=False, type=int),
            OpenApiParameter(name="language", description="Filtrer par code langue (ex: fr)", required=False, type=str),
            OpenApiParameter(name="ordering", description="Ex: datetime_start,-datetime_start", required=False, type=str),
        ],
        responses={200: EventSerializer, 401: OpenApiResponse(description="Non authentifié")},
    ),
    retrieve=extend_schema(
        tags=["Events"],
        description="Détail d’un événement (publié ou dont je suis le créateur).",
        responses={200: EventSerializer, 401: OpenApiResponse(description="Non authentifié"), 404: OpenApiResponse(description="Non trouvé")},
    ),
    create=extend_schema(
        tags=["Events"],
        description="Créer un événement (organisateur = user courant). Crée aussi un booking PENDING pour l’organisateur.",
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

    def get_permissions(self):
        if self.action in ("update", "partial_update", "destroy", "cancel"):
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

        user = self.request.user
        # Visibilité : PUBLISHED pour tous + MES événements (quel que soit le statut)
        if not getattr(user, "is_staff", False):
            qs = qs.filter(Q(status=Event.Status.PUBLISHED) | Q(organizer_id=user.id))
        return qs

    def perform_create(self, serializer):
        # 1) Créer l'évènement en DRAFT, organizer = request.user
        event = serializer.save(organizer=self.request.user, status=Event.Status.DRAFT)

        # 2) Créer le booking PENDING pour l'organisateur (montant = price_cents)
        Booking.objects.create(
            user=self.request.user,
            event=event,
            amount_cents=event.price_cents,
            currency="EUR",
        )

    def get_throttles(self):
        self.throttle_scope = "events_read" if self.action in ("list", "retrieve") else "events_write"
        return super().get_throttles()

    @extend_schema(
        tags=["Events"],
        summary="Annuler un événement (organisateur uniquement) et annuler tous les bookings liés.",
        responses={200: EventSerializer, 403: OpenApiResponse(description="Interdit"), 409: OpenApiResponse(description="Déjà annulé")},
    )
    @action(detail=True, methods=["POST"], url_path="cancel", url_name="cancel")
    def cancel(self, request, pk=None):
        event = self.get_object()  # IsOrganizerOrAdmin déjà contrôlé
        if event.status == Event.Status.CANCELLED:
            ser = self.get_serializer(event)
            return Response(ser.data, status=200)

        # 1) Annuler l'évènement
        event.mark_cancelled()

        # 2) Cascade sur TOUS les bookings liés (PENDING ou CONFIRMED) → CANCELLED
        now = timezone.now()
        qs = event.bookings.exclude(status=BookingStatus.CANCELLED)
        qs.update(status=BookingStatus.CANCELLED, cancelled_at=now, updated_at=now)

        ser = self.get_serializer(event)
        return Response(ser.data, status=200)
