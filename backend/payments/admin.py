from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "booking", "status", "amount_cents", "currency",
                    "stripe_checkout_session_id", "stripe_payment_intent_id", "created_at")
    list_filter = ("status", "currency", "created_at")
    search_fields = ("stripe_checkout_session_id", "stripe_payment_intent_id", "user__email", "booking__public_id")
    readonly_fields = ("created_at", "updated_at")
