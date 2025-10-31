"""
Django admin interface for audit logs.

Provides read-only access to audit logs with advanced filtering,
search, and colored display for better readability.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """
    Admin interface for AuditLog model.

    Features:
    - Read-only (no add/change/delete)
    - Advanced filtering by category, level, user, date
    - Search by action, message, path, IP
    - Colored display for categories and levels
    - Detailed metadata view
    """

    list_display = (
        "created_at",
        "category_colored",
        "level_colored",
        "action_short",
        "user_display",
        "resource_display",
        "status_code_colored",
        "duration_display",
    )

    list_filter = (
        "category",
        "level",
        "created_at",
        "status_code",
        ("user", admin.RelatedOnlyFieldListFilter),
        "resource_type",
    )

    search_fields = (
        "action",
        "message",
        "path",
        "user__email",
        "ip",
        "user_agent",
    )

    readonly_fields = (
        "category",
        "level",
        "action",
        "message",
        "user",
        "method",
        "path",
        "status_code",
        "ip",
        "user_agent",
        "duration_ms",
        "resource_type",
        "resource_id",
        "metadata_display",
        "created_at",
    )

    fieldsets = (
        ("Classification", {
            "fields": ("category", "level", "action", "message", "created_at")
        }),
        ("User Context", {
            "fields": ("user", "ip", "user_agent")
        }),
        ("HTTP Context", {
            "fields": ("method", "path", "status_code", "duration_ms"),
            "description": "Available for HTTP request logs"
        }),
        ("Business Context", {
            "fields": ("resource_type", "resource_id"),
            "description": "Available for business logic logs"
        }),
        ("Additional Data", {
            "fields": ("metadata_display",),
            "classes": ("collapse",)
        }),
    )

    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    list_per_page = 50

    # ====================================================================
    # CUSTOM DISPLAY METHODS
    # ====================================================================

    @admin.display(description="Category", ordering="category")
    def category_colored(self, obj):
        """Display category with color coding."""
        colors = {
            "HTTP": "#6c757d",        # Gray
            "AUTH": "#17a2b8",        # Cyan
            "EVENT": "#28a745",       # Green
            "BOOKING": "#ffc107",     # Amber
            "PAYMENT": "#fd7e14",     # Orange
            "PARTNER": "#6f42c1",     # Purple
            "USER": "#20c997",        # Teal
            "ADMIN": "#e83e8c",       # Pink
            "SYSTEM": "#343a40",      # Dark gray
        }
        color = colors.get(obj.category, "#000")
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 8px; border-radius: 3px; font-weight: bold; '
            'font-size: 11px;">{}</span>',
            color,
            obj.get_category_display()
        )

    @admin.display(description="Level", ordering="level")
    def level_colored(self, obj):
        """Display log level with color coding."""
        colors = {
            "DEBUG": "#6c757d",       # Gray
            "INFO": "#007bff",        # Blue
            "WARNING": "#ffc107",     # Yellow
            "ERROR": "#dc3545",       # Red
            "CRITICAL": "#721c24",    # Dark red
        }
        icons = {
            "DEBUG": "🔍",
            "INFO": "ℹ️",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "CRITICAL": "🚨",
        }
        color = colors.get(obj.level, "#000")
        icon = icons.get(obj.level, "")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color,
            icon,
            obj.level
        )

    @admin.display(description="Action", ordering="action")
    def action_short(self, obj):
        """Display action with truncation for long actions."""
        if len(obj.action) > 50:
            return format_html(
                '<span title="{}">{}</span>',
                obj.action,
                obj.action[:47] + "..."
            )
        return obj.action

    @admin.display(description="User", ordering="user")
    def user_display(self, obj):
        """Display user with link to user admin."""
        if obj.user:
            return format_html(
                '<a href="/admin/users/user/{}/change/">{}</a>',
                obj.user.id,
                obj.user.email
            )
        return format_html(
            '<span style="color: #6c757d; font-style: italic;">Anonymous</span>'
        )

    @admin.display(description="Resource")
    def resource_display(self, obj):
        """Display resource type and ID."""
        if obj.resource_type and obj.resource_id:
            return f"{obj.resource_type} #{obj.resource_id}"
        return "-"

    @admin.display(description="Status", ordering="status_code")
    def status_code_colored(self, obj):
        """Display HTTP status code with color coding."""
        if not obj.status_code:
            return "-"

        if obj.status_code >= 500:
            color = "#dc3545"  # Red
        elif obj.status_code >= 400:
            color = "#ffc107"  # Yellow
        elif obj.status_code >= 300:
            color = "#17a2b8"  # Cyan
        else:
            color = "#28a745"  # Green

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.status_code
        )

    @admin.display(description="Duration")
    def duration_display(self, obj):
        """Display duration with formatting."""
        if obj.duration_ms == 0:
            return "-"

        if obj.duration_ms < 100:
            color = "#28a745"  # Green (fast)
        elif obj.duration_ms < 500:
            color = "#ffc107"  # Yellow (medium)
        else:
            color = "#dc3545"  # Red (slow)

        return format_html(
            '<span style="color: {};">{} ms</span>',
            color,
            obj.duration_ms
        )

    @admin.display(description="Metadata")
    def metadata_display(self, obj):
        """Display metadata as formatted JSON."""
        if not obj.metadata:
            return mark_safe('<em style="color: #6c757d;">No metadata</em>')

        import json
        try:
            formatted = json.dumps(obj.metadata, indent=2, ensure_ascii=False)
            return format_html(
                '<pre style="background-color: #f8f9fa; padding: 10px; '
                'border-radius: 5px; overflow-x: auto;">{}</pre>',
                formatted
            )
        except Exception:
            return str(obj.metadata)

    # ====================================================================
    # PERMISSIONS (READ-ONLY)
    # ====================================================================

    def has_add_permission(self, request):
        """Prevent adding audit logs via admin."""
        return False

    def has_change_permission(self, request, obj=None):
        """Allow viewing but not changing audit logs."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deleting audit logs via admin."""
        return False
