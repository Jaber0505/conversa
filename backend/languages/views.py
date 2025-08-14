# backend/languages/views.py
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import AllowAny
from .models import Language
from .serializers import LanguageSerializer

class LanguageViewSet(ReadOnlyModelViewSet):
    queryset = Language.objects.filter(is_active=True).order_by("sort_order", "code")
    serializer_class = LanguageSerializer
    permission_classes = [AllowAny]
