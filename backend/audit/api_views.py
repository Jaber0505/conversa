"""
Audit log API views (RESTful).

Provides read-only access to audit logs for admins via REST API.
"""

from django.db.models import Count
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from .models import AuditLog
from .serializers import (
    AuditLogSerializer,
    AuditLogListSerializer,
    AuditLogStatsSerializer,
    AuditLogExportSerializer,
)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only API ViewSet for audit logs (admin only).

    Features:
    - Paginated list with filters (category, level, user, date)
    - Detailed view of specific log
    - Search by message, action
    - Sorting by date, category, level
    - Aggregated statistics
    - CSV export
    - Cleanup old logs
    """

    queryset = AuditLog.objects.select_related('user').all()
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    # Available filters
    filterset_fields = {
        'category': ['exact', 'in'],
        'level': ['exact', 'in'],
        'action': ['exact', 'icontains'],
        'user': ['exact'],
        'resource_type': ['exact'],
        'resource_id': ['exact'],
        'created_at': ['gte', 'lte', 'date'],
        'status_code': ['exact', 'gte', 'lte'],  # HTTP status code (200, 404, etc.)
        'method': ['exact'],                     # HTTP method (GET, POST, ...)
        'path': ['exact', 'icontains'],          # HTTP path
    }

    # Text search
    search_fields = ['message', 'action', 'user__email', 'ip']

    # Sorting
    ordering_fields = ['created_at', 'category', 'level', 'action']
    ordering = ['-created_at']  # Default: most recent first

    def get_serializer_class(self):
        """Use lightweight serializer for list, complete for detail."""
        if self.action == 'list':
            return AuditLogListSerializer
        return AuditLogSerializer

    @extend_schema(
        summary="List audit logs",
        description=(
            "Returns paginated list of audit logs with filters.\n\n"
            "**Available filters:**\n"
            "- `category`: HTTP, AUTH, EVENT, BOOKING, PAYMENT, PARTNER, USER, ADMIN, SYSTEM\n"
            "- `level`: DEBUG, INFO, WARNING, ERROR, CRITICAL\n"
            "- `user`: User ID\n"
            "- `created_at__gte`: Start date (format: YYYY-MM-DD)\n"
            "- `created_at__lte`: End date\n"
            "- `search`: Search in message, action, email\n\n"
            "**Example:**\n"
            "`/api/audit/?category=PAYMENT&level=ERROR&created_at__gte=2024-12-01`"
        ),
        parameters=[
            OpenApiParameter(name='category', description='Log category', required=False, type=str),
            OpenApiParameter(name='level', description='Severity level', required=False, type=str),
            OpenApiParameter(name='user', description='User ID', required=False, type=int),
            OpenApiParameter(name='created_at__gte', description='Start date', required=False, type=str),
            OpenApiParameter(name='search', description='Text search', required=False, type=str),
        ],
        responses={
            200: AuditLogListSerializer(many=True),
            403: OpenApiResponse(description="Access denied (admin only)"),
        },
        tags=['Audit'],
    )
    def list(self, request, *args, **kwargs):
        """Paginated list of audit logs."""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Audit log detail",
        description="Returns complete details of a log (includes JSON metadata)",
        responses={
            200: AuditLogSerializer,
            404: OpenApiResponse(description="Log not found"),
        },
        tags=['Audit'],
    )
    def retrieve(self, request, *args, **kwargs):
        """Audit log detail."""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Audit log statistics",
        description="Returns aggregated counters by category and level",
        responses={
            200: AuditLogStatsSerializer(many=True),
        },
        tags=['Audit'],
    )
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Aggregated log statistics.

        Returns counters by category and level.
        """
        # Aggregate by category and level
        stats = AuditLog.objects.values('category', 'level').annotate(
            count=Count('id')
        ).order_by('category', 'level')

        serializer = AuditLogStatsSerializer(stats, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Export audit logs to CSV",
        description=(
            "Exports logs to CSV format (same filters as list).\n\n"
            "**Format:** CSV with headers\n"
            "**Columns:** id, created_at, category, level, action, message, user_email, etc."
        ),
        responses={
            200: OpenApiResponse(description="CSV file"),
        },
        tags=['Audit'],
    )
    @action(detail=False, methods=['get'])
    def export(self, request):
        """
        CSV export of audit logs.

        Applies same filters as list.
        """
        import csv
        from django.http import HttpResponse

        # Filter queryset (same logic as list)
        queryset = self.filter_queryset(self.get_queryset())

        # Limit export to 10000 logs max (avoid timeout)
        queryset = queryset[:10000]

        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="audit_logs.csv"'

        writer = csv.writer(response)

        # Headers
        writer.writerow([
            'ID', 'Date', 'Category', 'Level', 'Action', 'Message',
            'User', 'Resource Type', 'Resource ID',
            'ip_address', 'http_method', 'http_path', 'http_status',
            'method', 'status_code'
        ])

        # Data
        for log in queryset:
            writer.writerow([
                log.id,
                log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                log.get_category_display(),
                log.get_level_display(),
                log.action,
                log.message,
                log.user.email if log.user else '',
                log.resource_type or '',
                log.resource_id or '',
                log.ip or '',
                getattr(log, 'method', '') or '',
                getattr(log, 'path', '') or '',
                getattr(log, 'status_code', '') or '',
                # Duplicate columns using model field names for convenience
                getattr(log, 'method', '') or '',
                getattr(log, 'status_code', '') or '',
            ])

        return response

    @extend_schema(
        summary="Cleanup old audit logs",
        description=(
            "Triggers cleanup of old audit logs based on retention policies.\n\n"
            "**Permissions:** Admin only\n\n"
            "**Use Case:**\n"
            "- Render Free Tier doesn't have cron jobs\n"
            "- Call this endpoint via GitHub Actions or manually\n"
            "- Runs cleanup_old_audits management command\n\n"
            "**Returns:**\n"
            "- 200: Cleanup successful with output\n"
            "- 500: Cleanup failed with error message"
        ),
        responses={
            200: OpenApiResponse(description="Cleanup successful"),
            500: OpenApiResponse(description="Cleanup failed"),
        },
        tags=['Audit'],
    )
    @action(detail=False, methods=['post'])
    def cleanup(self, request):
        """
        Trigger audit log cleanup based on retention policies.
        """
        from django.core.management import call_command
        from io import StringIO

        try:
            # Capture command output
            output = StringIO()
            call_command('cleanup_old_audits', stdout=output, verbosity=1)

            return Response({
                "status": "success",
                "message": "Audit cleanup completed",
                "output": output.getvalue()
            })
        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        summary="Purge audit logs (dev/admin)",
        description=(
            "Deletes audit logs matching current filters.\n\n"
            "Use this in development to purge test logs.\n\n"
            "Examples:\n"
            "- Purge TEST actions: POST /api/v1/audit/purge/?action__icontains=TEST\n"
            "- Purge HTTP logs: POST /api/v1/audit/purge/?category=HTTP\n"
        ),
        responses={
            200: OpenApiResponse(description="Purge completed"),
        },
        tags=['Audit'],
    )
    @action(detail=False, methods=['post'], url_path='purge')
    def purge(self, request):
        """
        Delete audit logs matching filters (admin-only utility for dev).
        """
        qs = self.filter_queryset(self.get_queryset())
        deleted, _ = qs.delete()
        return Response({
            "status": "success",
            "deleted": deleted
        })

    @extend_schema(
        summary="Dashboard audit statistics",
        description=(
            "Global statistics for admin dashboard.\n\n"
            "**Returns:**\n"
            "- Total logs count\n"
            "- Count by category\n"
            "- Count by level\n"
            "- Recent logs (last 24h)"
        ),
        responses={
            200: {
                'description': 'Global statistics',
                'examples': {
                    'application/json': {
                        'total_logs': 15234,
                        'by_category': {'PAYMENT': 523, 'AUTH': 1234},
                        'by_level': {'INFO': 12000, 'ERROR': 234},
                        'recent_logs_24h': 1234,
                    }
                }
            }
        },
        tags=['Audit'],
    )
    @action(detail=False, methods=['get'], url_path='dashboard-stats')
    def dashboard_stats(self, request):
        """
        Global statistics for admin dashboard.
        """
        from django.utils import timezone
        from datetime import timedelta

        # Total logs
        total = AuditLog.objects.count()

        # By category (list of dicts)
        by_category_qs = AuditLog.objects.values('category').annotate(count=Count('id'))
        by_category = list(by_category_qs)

        # By level (list of dicts)
        by_level_qs = AuditLog.objects.values('level').annotate(count=Count('id'))
        by_level = list(by_level_qs)

        # Logs last 24h
        last_24h = timezone.now() - timedelta(hours=24)
        recent_count = AuditLog.objects.filter(created_at__gte=last_24h).count()

        return Response({
            'total_logs': total,
            'by_category': by_category,
            'by_level': by_level,
            'recent_count_24h': recent_count,
        })
