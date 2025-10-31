"""
Audit log serializers for API.

Provides read-only access to audit logs for admin dashboard.
"""

from rest_framework import serializers
from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    """
    Serializer for AuditLog model (read-only).

    Includes all fields for comprehensive audit trail viewing.
    """

    user_email = serializers.CharField(source='user.email', read_only=True, allow_null=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    level_display = serializers.CharField(source='get_level_display', read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            'id',
            'created_at',
            'category',
            'category_display',
            'level',
            'level_display',
            'action',
            'message',
            'user',
            'user_email',
            'resource_type',
            'resource_id',
            'ip',
            'user_agent',
            'method',        # HTTP method (GET, POST, etc.)
            'path',          # HTTP path
            'status_code',   # HTTP status code
            'metadata',
        ]
        read_only_fields = fields  # All fields read-only


class AuditLogListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for audit log list view.

    Excludes heavy fields (metadata, user_agent) for performance.
    """

    user_email = serializers.CharField(source='user.email', read_only=True, allow_null=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    level_display = serializers.CharField(source='get_level_display', read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            'id',
            'created_at',
            'category',
            'category_display',
            'level',
            'level_display',
            'action',
            'message',
            'user',
            'user_email',
            'resource_type',
            'resource_id',
            'ip',
        ]
        read_only_fields = fields


class AuditLogStatsSerializer(serializers.Serializer):
    """
    Serializer for audit log statistics.

    Returns aggregated counts by category and level.
    """

    category = serializers.CharField()
    level = serializers.CharField()
    count = serializers.IntegerField()


class AuditLogExportSerializer(serializers.ModelSerializer):
    """
    Serializer for CSV export.

    Flattens nested fields for easier CSV export.
    """

    user_email = serializers.CharField(source='user.email', read_only=True, allow_null=True)
    category_name = serializers.CharField(source='get_category_display', read_only=True)
    level_name = serializers.CharField(source='get_level_display', read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            'id',
            'created_at',
            'category_name',
            'level_name',
            'action',
            'message',
            'user_email',
            'resource_type',
            'resource_id',
            'ip',
            'method',        # HTTP method
            'path',          # HTTP path
            'status_code',   # HTTP status code
        ]
        read_only_fields = fields
