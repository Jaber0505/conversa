from django.urls import path
from users.views.me import MeView
from users.views.badge import UserBadgesView
from users.views.preferences import UserPreferencesView

urlpatterns = [
    path("me/", MeView.as_view(), name="me"),
    path("me/badges/", UserBadgesView.as_view(), name="me-badges"),
    path("me/preferences/", UserPreferencesView.as_view(), name="me-preferences"),
]
