from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from drf_spectacular.utils import extend_schema
from users.permissions.base import IsAuthenticatedAndActive


@extend_schema(
    summary="Ping authentification",
    description="Retourne un code 200 si le token d’authentification est valide. Sinon 401.",
    tags=["Utilisateurs"],
    methods=["HEAD"],
    responses={200: None, 401: None}
)
class PingAuthView(APIView):
    permission_classes = [IsAuthenticatedAndActive]

    def head(self, request):
        return Response(status=status.HTTP_200_OK)
