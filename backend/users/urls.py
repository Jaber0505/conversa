from django.urls import path
from users.views import (
    RegisterView,
    MeView,
    ExportDataView,
    PublicUserProfileView,
    RequestPasswordResetView,
    ConfirmPasswordResetView,
)

from users.views.jwt import (
    SpectacularTokenObtainPairView,
    SpectacularTokenRefreshView,
    PingAuthView, 
    LogoutView,
)

urlpatterns = [
    # Authentification
    path("auth/token/", SpectacularTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", SpectacularTokenRefreshView.as_view(), name="token_refresh"),
    path("auth/ping/", PingAuthView.as_view(), name="auth-ping"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),

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
