from django.urls import path
from .views import RegisterView, EmailLoginView, RefreshView, LogoutView, MeView, PasswordResetRequestView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/",    EmailLoginView.as_view(), name="auth-login"),
    path("refresh/",  RefreshView.as_view(),    name="auth-refresh"),
    path("logout/",   LogoutView.as_view(),     name="auth-logout"),
    path("me/",       MeView.as_view(),         name="auth-me"),
    path("password-reset/", PasswordResetRequestView.as_view(), name="auth-password-reset"),
]
