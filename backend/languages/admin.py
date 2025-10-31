"""Django admin configuration for Language model."""
from django.contrib import admin
from .models import Language


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    """Admin interface for managing languages."""

    search_fields = ("code", "label_fr", "label_en", "label_nl")  # Required for autocomplete
    list_display = ("code", "label_en", "label_fr", "label_nl", "is_active", "sort_order")
    list_filter = ("is_active",)
    list_editable = ("is_active", "sort_order")
    ordering = ("sort_order", "code")
    readonly_fields = ("created_at",)

    fieldsets = (
        ("Identification", {
            "fields": ("code",)
        }),
        ("Labels", {
            "fields": ("label_en", "label_fr", "label_nl")
        }),
        ("Settings", {
            "fields": ("is_active", "sort_order")
        }),
        ("Metadata", {
            "fields": ("created_at",),
            "classes": ("collapse",)
        }),
    )
