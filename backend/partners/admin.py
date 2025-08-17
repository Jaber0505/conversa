from django.contrib import admin
from .models import Partner

@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ("name", "address", "reputation", "api_key", "created_at")
    search_fields = ("name", "address")
    readonly_fields = ("api_key", "created_at", "updated_at")
