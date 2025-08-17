# backend/config/urls.py
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

def healthz(_request):
    return HttpResponse("ok", content_type="text/plain")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz", healthz),

    # OpenAPI / Swagger
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),

    path("api/v1/auth/", include("users.urls")),
    path("api/v1/languages/", include("languages.urls")),
    path("api/v1/events/", include("events.urls")),
    #path("api/v1/bookings/", include("bookings.urls")),
    #path("api/v1/payments/", include("payments.urls")),
    path("api/v1/partners/", include("partners.urls")),
]
