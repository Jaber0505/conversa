"""
Main URL configuration for Conversa API.

This module defines all API routes including:
- Admin panel
- Health check endpoint
- API documentation (Swagger/ReDoc)
- Versioned API endpoints (v1)
"""

from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)


def healthz(_request):
    """
    Health check endpoint for monitoring and load balancers.

    Returns:
        HttpResponse: Simple "ok" response
    """
    return HttpResponse("ok", content_type="text/plain")


urlpatterns = [
    # Admin interface
    path("admin/", admin.site.urls),

    # Health check
    path("healthz", healthz, name="healthz"),

    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),

    # API v1 Routes
    path("api/v1/auth/", include("users.urls")),
    path("api/v1/languages/", include("languages.urls")),
    path("api/v1/events/", include("events.urls")),
    path("api/v1/bookings/", include("bookings.urls")),
    path("api/v1/payments/", include(("payments.urls", "payments"), namespace="payments")),
    path("api/v1/partners/", include("partners.urls")),
    # Registrations removed: draft events are private, no free registrations
    path("api/v1/audit/", include("audit.urls")),  # Audit management (admin only)
]
