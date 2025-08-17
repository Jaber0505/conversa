from django.contrib import admin
from .models import Booking

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "event", "user", "status", "created_at")
    list_filter = ("status", "event")
    search_fields = ("user__email", "user__username")
