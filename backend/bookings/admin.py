from django.contrib import admin
from .models import Booking

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "id", "public_id", "user", "event", "status",
        "amount_cents", "currency",
        "expires_at", "confirmed_at", "cancelled_at", "created_at",
    )
    list_filter = ("status", "currency", "created_at")
    search_fields = ("public_id", "user__email", "event__title", "payment_intent_id")
    readonly_fields = ("public_id", "created_at", "updated_at", "confirmed_at", "cancelled_at")
