from django.contrib import admin
from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "theme",
        "partner",
        "language",
        "datetime_start",
        "organizer",
        "status",
        "price_cents",
        "published_at",
        "created_at",
    )
    list_filter = ("status", "language", "partner", "difficulty")
    search_fields = ("title", "theme", "partner__name", "language__code")
    ordering = ("-datetime_start",)
    readonly_fields = ("price_cents", "title", "address", "status", "published_at", "cancelled_at", "created_at", "updated_at")
