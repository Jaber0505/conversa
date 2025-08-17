from django.contrib import admin
from .models import Booking

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "public_id", "user", "event", "status", "quantity", "amount_cents", "currency", "created_at")
    list_filter = ("status", "currency", "created_at")
    search_fields = ("public_id", "user__email", "event__title", "payment_intent_id")
