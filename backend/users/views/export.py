from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from users.permissions.base import IsSelf
from users.serializers import UserMeSerializer
from drf_spectacular.utils import extend_schema, OpenApiResponse

@extend_schema(
    summary="Exporter les données personnelles de l’utilisateur connecté",
    description="Permet à l’utilisateur d’obtenir toutes ses données personnelles au format JSON, conformément au RGPD.",
    responses={200: OpenApiResponse(description="Export JSON réussi")},
)
class ExportDataView(APIView):
    permission_classes = [IsAuthenticated, IsSelf]

    def get(self, request):
        self.check_object_permissions(request, request.user)

        data = UserMeSerializer(request.user, context={"request": request}).data
        return Response({"export": data})
