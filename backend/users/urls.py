from django.urls import path
from users.views import (
    RegisterView,
    MeView,
    ExportDataView,
    PublicUserProfileView,
    RequestPasswordResetView,
    ConfirmPasswordResetView,
)

from users.views.auth import (
    PingAuthView, 
    LogoutView,
    CustomTokenObtainPairView,
    CustomTokenRefreshView
)

from drf_spectacular.views import SpectacularAPIView
from drf_spectacular.openapi import AutoSchema


from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny



class CustomSpectacularAPIView(SpectacularAPIView):
    schema = AutoSchema()

class PingView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            "status": "ok",
            "message": "Backend opérationnel – communication établie ✅"
        })

urlpatterns = [
    # Authentification
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', LogoutView.as_view(), name='auth_logout'),
    path('auth/ping/', PingAuthView.as_view(), name='auth_ping'),

    # Utilisateur connecté
    path("users/me/", MeView.as_view(), name="user-me"),
    path("users/me/export/", ExportDataView.as_view(), name="user-export"),

    # Inscription
    path("users/register/", RegisterView.as_view(), name="user-register"),

    # Profils publics
    path("users/<int:pk>/public/", PublicUserProfileView.as_view(), name="user-public"),

    # Password reset
    path("users/reset-password/", RequestPasswordResetView.as_view(), name="reset-password"),
    path("users/reset-password/confirm/", ConfirmPasswordResetView.as_view(), name="reset-password-confirm"),

    path("ping", PingView.as_view(), name="ping"),
]
