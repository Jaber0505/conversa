# backend/audit/admin.py
from django.contrib import admin
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user", "method", "path", "status_code", "duration_ms", "ip")
    list_filter = ("method", "status_code", "created_at")
    search_fields = ("path", "user__username", "ip", "user_agent")
    readonly_fields = ("user", "method", "path", "status_code", "ip", "user_agent", "duration_ms", "created_at")

    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
