from rest_framework.views import APIView
from rest_framework.response import Response

from users.permissions.base import IsSelf, IsAuthenticatedAndActive
from users.serializers import UserMeSerializer

from drf_spectacular.utils import extend_schema, OpenApiResponse

@extend_schema(
    summary="Exporter les données personnelles de l’utilisateur",
    description="""
        Ce endpoint permet à l’utilisateur connecté d’exporter toutes ses données personnelles 
        au format JSON, en conformité avec le RGPD.  
        Les données retournées incluent les informations de profil stockées dans la base de données.
    """,
    responses={
        200: OpenApiResponse(
            description="Données exportées avec succès (format JSON)",
            response=None,  # on ne précise pas le serializer pour laisser la réponse libre
        ),
        403: OpenApiResponse(description="Accès interdit (utilisateur non autorisé)"),
    },
    tags=["Utilisateurs"]
)
class ExportDataView(APIView):
    permission_classes = [IsAuthenticatedAndActive, IsSelf]

    def get(self, request):
        self.check_object_permissions(request, request.user)
        data = UserMeSerializer(request.user, context={"request": request}).data
        return Response({"export": data})
