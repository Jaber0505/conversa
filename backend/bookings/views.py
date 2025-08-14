# backend/bookings/views.py
from rest_framework import generics, permissions
from .models import Booking
from .serializers import BookingCreateSerializer, BookingSerializer

class BookingCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BookingCreateSerializer

class MyBookingsView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BookingSerializer

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user).order_by("-created_at")
