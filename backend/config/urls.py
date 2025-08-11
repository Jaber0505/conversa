# config/urls.py
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

def healthz(_request):
    return JsonResponse({"status": "ok", "message": "Backend opérationnel"})

urlpatterns = [
    path("admin/", admin.site.urls),

    # Health check
    path("healthz/", healthz, name="healthz"),

    # OpenAPI (Swagger/ReDoc)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/docs/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),

    # API v1
    path("api/v1/", include("users.urls", namespace="users")),
    path("api/v1/", include("languages.urls", namespace="languages")),
]
