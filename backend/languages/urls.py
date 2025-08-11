# languages/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from languages.views.language import LanguageViewSet

app_name = "languages"

router = DefaultRouter()
router.register(r"languages", LanguageViewSet, basename="language")

urlpatterns = [path("", include(router.urls))]