from django.contrib import admin
from .models import Language

@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    search_fields = ("code", "label_fr", "label_en", "label_nl")  # requis pour autocomplete
    list_display = ("code", "label_fr", "is_active", "sort_order")
    list_filter = ("is_active",)
    ordering = ("sort_order", "code")
