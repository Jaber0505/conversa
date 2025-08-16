from django.urls import path
from .views import RegisterView, EmailLoginView, RefreshView, LogoutView, MeView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/",    EmailLoginView.as_view(), name="auth-login"),
    path("refresh/",  RefreshView.as_view(),    name="auth-refresh"),
    path("logout/",   LogoutView.as_view(),     name="auth-logout"),
    path("me/",       MeView.as_view(),         name="auth-me"),
]
