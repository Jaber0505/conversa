# backend/bookings/urls.py
from django.urls import path
from .views import BookingCreateView, MyBookingsView

urlpatterns = [
    path("", BookingCreateView.as_view(), name="booking-create"),
    path("mine/", MyBookingsView.as_view(), name="booking-mine"),
]
