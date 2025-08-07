import uuid

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
@extend_schema(
    methods=["DELETE"],
    summary="Supprimer son compte (RGPD)",
    description="""
        Cette route permet à l’utilisateur connecté de supprimer son compte.  
        Les données personnelles sont anonymisées.
        Le compte est désactivé, conformément au RGPD.  
        Toutes les sessions sont invalidées immédiatement.
    """,
    responses={
        200: OpenApiResponse(description="Compte supprimé avec succès."),
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

    def delete(self, request):
        user = request.user

        user.email = f"deleted_{user.pk}@deleted.local"
        user.first_name = ""
        user.last_name = ""
        user.bio = ""
        user.languages_spoken = []
        user.is_profile_public = False
        user.consent_given = False
        user.is_active = False
        user.jwt_key = uuid.uuid4()

        user.save()

        return Response(
            {"detail": "Votre compte a été supprimé conformément au RGPD."},
            status=200
        )

