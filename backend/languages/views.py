from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse

from .models import Language
from .serializers import LanguageSerializer
from common.mixins import HateoasOptionsMixin
from common.metadata import HateoasMetadata


@extend_schema_view(
    list=extend_schema(
        summary="List available languages",
        description=(
            "Returns list of all active languages available on the platform.\n\n"
            "Languages are used for:\n"
            "- User profiles (native and target languages)\n"
            "- Event language specification\n\n"
            "**Permissions:** Public (no authentication required)\n\n"
            "**Returns:** Languages ordered by sort_order and code"
        ),
        responses={
            200: LanguageSerializer(many=True),
        },
    ),
    retrieve=extend_schema(
        summary="Get language details",
        description=(
            "Returns details of a specific language by ID.\n\n"
            "Includes translations in French, English, and Dutch."
        ),
        responses={
            200: LanguageSerializer,
            404: OpenApiResponse(description="Language not found"),
        },
    ),
)
@extend_schema(tags=["Languages"])
class LanguageViewSet(HateoasOptionsMixin, ReadOnlyModelViewSet):
    """
    Read-only ViewSet for available languages.

    Provides list and detail views for languages available on the platform.
    No authentication required - this is public data.
    """
    queryset = Language.objects.filter(is_active=True).order_by("sort_order", "code")
    serializer_class = LanguageSerializer
    permission_classes = [AllowAny]
    metadata_class = HateoasMetadata

    extra_hateoas = {"related": {"self": "/api/v1/languages/"}}
