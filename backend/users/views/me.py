from rest_framework.views import APIView
from rest_framework.response import Response

from users.serializers import UserMeSerializer, UserMeUpdateSerializer
from users.permissions import IsAuthenticatedAndActive

from drf_spectacular.utils import extend_schema, OpenApiResponse

@extend_schema(
    summary="Afficher le profil de l'utilisateur connecté",
    description="""
        Retourne les informations personnelles de l’utilisateur connecté.  
        Ce profil inclut des champs non sensibles ainsi que des liens HATEOAS
        pour interagir avec l’API (édition, export, etc.).
    """,
    responses={200: UserMeSerializer},
    tags=["Utilisateurs"]
)
@extend_schema(
    methods=["PATCH"],
    summary="Mettre à jour le profil utilisateur",
    description="""
        Permet à l’utilisateur connecté de modifier certains champs autorisés
        de son profil : prénom, nom, bio et langues pratiquées.
    """,
    request=UserMeUpdateSerializer,
    responses={
        200: OpenApiResponse(response=UserMeSerializer, description="Profil mis à jour avec succès"),
        400: OpenApiResponse(description="Erreur de validation des données"),
    },
    tags=["Utilisateurs"]
)
class MeView(APIView):
    permission_classes = [IsAuthenticatedAndActive]

    def get(self, request):
        serializer = UserMeSerializer(request.user, context={"request": request})
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserMeUpdateSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            UserMeSerializer(request.user, context={"request": request}).data
        )
