from datetime import timedelta
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse

from .models import Booking
from .serializers import BookingSerializer
from events.models import Event 


@extend_schema_view(
    list=extend_schema(summary="Lister mes réservations ou celles d'un event si autorisé"),
    retrieve=extend_schema(summary="Détail d'une réservation"),
    create=extend_schema(summary="Créer une réservation"),
)
class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        - Par défaut : l'utilisateur voit SEULEMENT ses bookings.
        - Si ?event=<id> ET user est organisateur de cet event (ou admin) :
          retourne les bookings de cet event.
        """
        qs = Booking.objects.select_related("event", "user", "event__partner")
        event_id = self.request.query_params.get("event")
        if event_id:
            try:
                ev = Event.objects.select_related("organizer").get(pk=event_id)
            except Event.DoesNotExist:
                return Booking.objects.none()
            if self.request.user.is_staff or ev.organizer_id == self.request.user.id:
                return qs.filter(event_id=event_id)
            return Booking.objects.none()
        return qs.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save()  # user injecté dans le serializer

    @extend_schema(
        summary="Annuler ma réservation (jusqu'à T-3h)",
        responses={
            200: OpenApiResponse(response=BookingSerializer, description="Réservation annulée"),
            400: OpenApiResponse(description="Trop tard pour annuler (< 3h) ou statut invalide"),
            403: OpenApiResponse(description="Interdit"),
        },
    )
    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        booking = self.get_object()
        if booking.user != request.user:
            return Response({"detail": "Vous ne pouvez annuler que votre propre réservation."},
                            status=status.HTTP_403_FORBIDDEN)

        if timezone.now() > booking.event.datetime_start - timedelta(hours=3):
            return Response({"detail": "Annulation impossible < 3h avant l'événement."},
                            status=status.HTTP_400_BAD_REQUEST)

        if booking.status != "confirmed":
            return Response({"detail": "La réservation n'est pas confirmée."},
                            status=status.HTTP_400_BAD_REQUEST)

        booking.status = "cancelled_user"
        booking.save(update_fields=["status", "updated_at"])
        return Response(self.get_serializer(booking).data, status=status.HTTP_200_OK)
