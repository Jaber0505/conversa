"""
Audit URL configuration.

Provides admin-only endpoints for audit management and RESTful API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import AuditLogViewSet

# Router for RESTful API
router = DefaultRouter()
router.register(r'', AuditLogViewSet, basename='audit-log')

urlpatterns = [
    # RESTful API endpoints:
    # GET /api/v1/audit/ - List logs
    # GET /api/v1/audit/{id}/ - Log detail
    # GET /api/v1/audit/stats/ - Statistics
    # GET /api/v1/audit/export/ - CSV export
    # POST /api/v1/audit/cleanup/ - Cleanup old logs
    # GET /api/v1/audit/dashboard-stats/ - Dashboard statistics
    path('', include(router.urls)),
]
