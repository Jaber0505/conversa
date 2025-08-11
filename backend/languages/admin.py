# languages/admin.py
from django.contrib import admin
from .models import Language

@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ("code", "is_active", "sort_order", "updated_at")
    search_fields = ("code",)
    list_filter = ("is_active",)
    ordering = ("sort_order", "code")

