from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import NotFound

from users.models import User
from users.serializers import PublicUserSerializer
from drf_spectacular.utils import extend_schema, OpenApiResponse


@extend_schema(
    summary="Voir le profil public d’un utilisateur",
    description=(
        "Ce endpoint permet de consulter les informations publiques d’un utilisateur via son ID. "
        "Si le profil est privé ou inexistant, une erreur 404 est renvoyée."
    ),
    responses={
        200: PublicUserSerializer,
        404: OpenApiResponse(description="Profil inexistant ou privé."),
    },
    tags=["Utilisateurs"],
)
class PublicUserProfileView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        user = User.objects.filter(pk=pk, is_profile_public=True).first()
        if not user:
            raise NotFound("Ce profil est privé ou inexistant.")
        serializer = PublicUserSerializer(user, context={"request": request})
        return Response(serializer.data)
