"""
Fichier principal des routes Django.
- /admin/ : interface d'administration
- /healthz : vérification rapide de l'état du backend (Render, monitoring)
- /api/schema/ : schéma OpenAPI (Swagger/ReDoc)
- /api/v1/... : endpoints REST (versionnés)
"""

from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

# Endpoint health check (Prod & Dev)
def healthz(request):
    return JsonResponse({"status": "ok", "message": "Backend opérationnel"})

urlpatterns = [
    # Admin Django
    path("admin/", admin.site.urls),

    # Health check
    path("healthz", healthz),

    # API schema (OpenAPI)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/swagger/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/docs/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),

    # API v1 (inclut les routes de l'app users)
    path("api/v1/", include("users.urls")),
]
