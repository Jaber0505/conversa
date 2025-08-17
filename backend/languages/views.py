from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema

from .models import Language
from .serializers import LanguageSerializer
from common.mixins import HateoasOptionsMixin
from common.metadata import HateoasMetadata


@extend_schema(tags=["Languages"])
class LanguageViewSet(HateoasOptionsMixin, ReadOnlyModelViewSet):
    queryset = Language.objects.filter(is_active=True).order_by("sort_order", "code")
    serializer_class = LanguageSerializer
    permission_classes = [AllowAny]
    metadata_class = HateoasMetadata

    extra_hateoas = {"related": {"self": "/api/v1/languages/"}}
