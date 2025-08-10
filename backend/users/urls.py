# users/urls.py
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
    CustomTokenRefreshView,
)

app_name = "users"

urlpatterns = [
    # Auth
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/token/", CustomTokenObtainPairView.as_view(), name="token-obtain"),
    path("auth/token/refresh/", CustomTokenRefreshView.as_view(), name="token-refresh"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("auth/ping/", PingAuthView.as_view(), name="auth-ping"),
    path("auth/reset-password/", RequestPasswordResetView.as_view(), name="auth-reset"),
    path("auth/reset-password/confirm/", ConfirmPasswordResetView.as_view(), name="auth-reset-confirm"),

    # Utilisateur courant
    path("users/me/", MeView.as_view(), name="user-me"),
    path("users/me/export/", ExportDataView.as_view(), name="user-export"),

    # Profils publics
    path("users/<int:pk>/public/", PublicUserProfileView.as_view(), name="user-public"),
]
