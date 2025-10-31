"""Django admin configuration for Partner model."""
from django.contrib import admin
from django.utils.html import format_html
from .models import Partner


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    """Admin interface for managing partner venues."""

    list_display = (
        "name",
        "city",
        "capacity",
        "reputation_display",
        "is_active",
        "api_key_preview",
        "created_at"
    )
    list_filter = ("is_active", "city", "reputation")
    list_editable = ("is_active",)
    search_fields = ("name", "address", "city")
    readonly_fields = ("api_key", "created_at", "updated_at")
    ordering = ("-created_at",)

    fieldsets = (
        ("Basic Information", {
            "fields": ("name", "address", "city")
        }),
        ("Capacity & Rating", {
            "fields": ("capacity", "reputation", "is_active")
        }),
        ("Security", {
            "fields": ("api_key",),
            "classes": ("collapse",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def reputation_display(self, obj):
        """Display reputation with stars."""
        stars = "⭐" * int(obj.reputation)
        return f"{obj.reputation} {stars}"
    reputation_display.short_description = "Reputation"

    def api_key_preview(self, obj):
        """Display truncated API key."""
        if obj.api_key:
            return format_html(
                '<code>{}...{}</code>',
                obj.api_key[:8],
                obj.api_key[-8:]
            )
        return "-"
    api_key_preview.short_description = "API Key"
