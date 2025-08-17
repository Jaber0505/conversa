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
        "price_cents",
        "created_at",
    )
    list_filter = ("language", "partner", "difficulty")
    search_fields = ("title", "theme", "partner__name", "language__code")
    ordering = ("-datetime_start",)
    readonly_fields = ("price_cents", "title", "address", "created_at", "updated_at")
