from django.utils import timezone
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from .models import Booking, BookingStatus
from .serializers import BookingSerializer, BookingCreateSerializer
from common.permissions import IsAuthenticatedAndActive


class BookingViewSet(mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.DestroyModelMixin,
                     mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    permission_classes = [IsAuthenticatedAndActive]
    lookup_field = "public_id"
    lookup_value_regex = r"[0-9a-fA-F-]{36}"

    def get_queryset(self):
        """
        Get user's bookings with optional filtering.

        ARCHITECTURE RULE:
        Auto-expiration is handled by background task (celery).
        Views should NOT contain business logic.
        """
        # Scope to user's bookings only
        qs = Booking.objects.select_related("event").filter(user=self.request.user)

        # Optional filter by status
        status_param = self.request.query_params.get("status")
        valid_status = {c for c, _ in BookingStatus.choices}
        if status_param in valid_status:
            qs = qs.filter(status=status_param)

        # Optional filter by event
        event_id = self.request.query_params.get("event")
        if event_id:
            qs = qs.filter(event_id=event_id)

        return qs

    def get_serializer_class(self):
        if self.action == "create":
            return BookingCreateSerializer
        return BookingSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(name="status", description="Filtrer par statut", required=False,
                             type=str, enum=[c for c, _ in BookingStatus.choices]),
            OpenApiParameter(name="event", description="Filtrer par ID d’évènement", required=False, type=int),
        ],
        responses={200: BookingSerializer(many=True)},
        summary="Lister MES réservations",
        tags=["Bookings"],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        request=BookingCreateSerializer,
        responses={201: BookingSerializer, 400: OpenApiResponse(description="Validation")},
        summary="Créer une réservation (au nom de l’utilisateur courant)",
        tags=["Bookings"],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        responses={200: BookingSerializer, 404: OpenApiResponse(description="Not found")},
        summary="Détail d’UNE de mes réservations",
        tags=["Bookings"],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        responses={204: OpenApiResponse(description="Annulé"), 409: OpenApiResponse(description="Déjà confirmée")},
        summary="Annuler via DELETE (réservation non confirmée uniquement)",
        tags=["Bookings"],
    )
    def destroy(self, request, *args, **kwargs):
        """
        Cancel booking via DELETE.

        ARCHITECTURE RULE:
        Delegates to BookingService for business logic validation.
        """
        from .services import BookingService
        from common.exceptions import CancellationDeadlineError

        booking = get_object_or_404(self.get_queryset(), public_id=kwargs.get(self.lookup_field))

        # Delegate to BookingService (SINGLE SOURCE OF TRUTH)
        if not BookingService.can_cancel_booking(booking):
            return Response(
                {"detail": "Réservation déjà confirmée ou impossible à annuler."},
                status=status.HTTP_409_CONFLICT
            )

        try:
            BookingService.cancel_booking(booking, cancelled_by=request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except CancellationDeadlineError as e:
            return Response({"detail": str(e)}, status=status.HTTP_409_CONFLICT)

    @extend_schema(
        responses={200: BookingSerializer, 409: OpenApiResponse(description="Impossible d'annuler")},
        summary="Annuler explicitement (POST /cancel/)",
        tags=["Bookings"],
    )
    @action(detail=True, methods=["POST"])
    def cancel(self, request, public_id=None):
        from .services import BookingService
        from common.exceptions import CancellationDeadlineError

        booking = self.get_object()  # déjà scope user

        # Check if already cancelled
        if booking.status == BookingStatus.CANCELLED:
            return Response({"detail": "Réservation déjà annulée."}, status=409)

        try:
            # Use BookingService which handles both PENDING and CONFIRMED with proper deadline validation
            BookingService.cancel_booking(booking, cancelled_by=request.user)
            booking.refresh_from_db()
            ser = BookingSerializer(booking, context={"request": request})
            return Response(ser.data, status=200)
        except CancellationDeadlineError as e:
            return Response({"detail": str(e)}, status=409)
