# backend/events/views.py
from rest_framework import permissions
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny, IsAuthenticated
from common.permissions import IsOrganizerOrReadOnly
from .models import Event
from .serializers import EventSerializer, EventWriteSerializer

class EventViewSet(ModelViewSet):
    queryset = Event.objects.order_by("-datetime_start")
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [AllowAny()]
        return [IsAuthenticated(), IsOrganizerOrReadOnly()]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return EventWriteSerializer
        return EventSerializer

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)
