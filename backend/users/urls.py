from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from users.views import (
    RegisterView,
    MeView,
    ExportDataView,
    PublicUserProfileView,
    PingAuthView,
    RequestPasswordResetView, 
    ConfirmPasswordResetView
)

urlpatterns = [
    # Authentification
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/ping/", PingAuthView.as_view(), name="auth-ping"),

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
]
