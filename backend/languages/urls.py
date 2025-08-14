# backend/languages/urls.py
from rest_framework.routers import DefaultRouter
from .views import LanguageViewSet

router = DefaultRouter()
router.register("", LanguageViewSet, basename="language")
urlpatterns = router.urls
