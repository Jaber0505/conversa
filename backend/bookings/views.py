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
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticatedAndActive]
    lookup_field = "public_id"
    lookup_value_regex = r"[0-9a-fA-F-]{36}"

    def get_queryset(self):
        qs = Booking.objects.select_related("event").filter(user=self.request.user)
        now = timezone.now()
        expired = qs.filter(status=BookingStatus.PENDING, expires_at__lte=now)
        if expired.exists():
            expired.update(status=BookingStatus.CANCELLED, cancelled_at=now, updated_at=now)
        return Booking.objects.select_related("event").filter(user=self.request.user)

    def get_object(self):
        return get_object_or_404(
            Booking.objects.select_related("event").filter(user=self.request.user),
            public_id=self.kwargs.get(self.lookup_field),
        )

    @extend_schema(
        request=BookingCreateSerializer,
        responses={201: BookingSerializer},
        summary="Créer une réservation (PENDING)",
        tags=["Bookings"],
    )
    def create(self, request, *args, **kwargs):
        ser = BookingCreateSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        booking = ser.save()
        out = BookingSerializer(booking, context={"request": request})
        return Response(out.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        parameters=[OpenApiParameter(name="status", description="Filtrer par statut", required=False, type=str)],
        responses={200: BookingSerializer(many=True)},
        summary="Lister mes réservations",
        tags=["Bookings"],
    )
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        status_param = request.query_params.get("status")
        if status_param in {c.value for c in BookingStatus}:
            queryset = queryset.filter(status=status_param)
        page = self.paginate_queryset(queryset)
        if page is not None:
            ser = BookingSerializer(page, many=True, context={"request": request})
            return self.get_paginated_response(ser.data)
        ser = BookingSerializer(queryset, many=True, context={"request": request})
        return Response(ser.data)

    @extend_schema(
        responses={200: BookingSerializer},
        summary="Détail de ma réservation (par public_id)",
        tags=["Bookings"],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        responses={204: OpenApiResponse(description="Annulée"), 409: OpenApiResponse(description="Déjà confirmée")},
        summary="Annuler (DELETE) si PENDING",
        tags=["Bookings"],
    )
    def destroy(self, request, *args, **kwargs):
        booking = self.get_object()
        if booking.status == BookingStatus.CONFIRMED:
            return Response({"detail": "Impossible d’annuler une réservation confirmée."}, status=409)
        booking.mark_cancelled()
        return Response(status=204)

    @extend_schema(
        responses={200: BookingSerializer, 409: OpenApiResponse(description="Déjà confirmée")},
        summary="Annuler explicitement",
        tags=["Bookings"],
    )
    @action(detail=True, methods=["POST"])
    def cancel(self, request, public_id=None):
        booking = self.get_object()
        if booking.status == BookingStatus.CONFIRMED:
            return Response({"detail": "Réservation déjà confirmée."}, status=409)
        booking.mark_cancelled()
        ser = BookingSerializer(booking, context={"request": request})
        return Response(ser.data, status=200)
