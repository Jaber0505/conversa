from datetime import timedelta
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from drf_spectacular.utils import extend_schema
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from common.permissions import IsAuthenticatedAndActive
from .models import Event
from .serializers import EventSerializer


@extend_schema(tags=["Events"])
class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticatedAndActive]

    # ---- Filtres / Search / Ordering ----
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        "language__code": ["exact"],            # ?language__code=fr
        "partner__city": ["exact"],             # ?partner__city=Bruxelles
        "price_cents": ["gte", "lte"],          # ?price_cents__lte=700
        "partner__reputation": ["gte", "lte"],  # ?partner__reputation__gte=4.0
        "theme": ["exact"],                     # ?theme=Afterwork test
    }
    search_fields = ["theme"]                   # ?search=afterwork
    ordering_fields = ["datetime_start", "price_cents", "partner__reputation"]

    def get_queryset(self):
        """
        Utilisateur normal → événements non annulés
        Admin → tous
        """
        qs = Event.objects.all()
        if not self.request.user.is_staff:
            qs = qs.exclude(status="cancelled")
        return qs

    def perform_create(self, serializer):
        # Organisateur auto = utilisateur connecté
        serializer.save(organizer=self.request.user)

    def perform_update(self, serializer):
        # Seul l’organisateur ou un admin peut modifier
        event = self.get_object()
        if self.request.user != event.organizer and not self.request.user.is_staff:
            raise PermissionDenied("Non autorisé à modifier cet événement.")
        serializer.save()

    def perform_destroy(self, instance):
        """
        Soft delete = annulation.
        Règle métier : impossible < T−3h.
        """
        if self.request.user != instance.organizer and not self.request.user.is_staff:
            raise PermissionDenied("Non autorisé à annuler cet événement.")
        if timezone.now() > instance.datetime_start - timedelta(hours=3):
            raise ValidationError("Annulation impossible moins de 3h avant l'événement.")
        instance.status = "cancelled"
        instance.save(update_fields=["status", "updated_at"])
