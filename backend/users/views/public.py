from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import NotFound

from users.models import User
from users.serializers import PublicUserSerializer
from drf_spectacular.utils import extend_schema, OpenApiResponse

@extend_schema(
    summary="Voir un profil utilisateur public",
    description="""
        Ce endpoint permet de consulter les informations publiques d’un utilisateur à partir de son identifiant (`pk`).

        Le profil doit être marqué comme **public** (`is_profile_public=True`) pour être accessible.
        
        Si le profil n’existe pas ou est privé, une erreur `404 Not Found` est renvoyée.

        ✅ Aucun token n’est requis. Accessible même en étant déconnecté.
    """,
    responses={
        200: PublicUserSerializer,
        404: OpenApiResponse(description="Profil inexistant ou privé.")
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
