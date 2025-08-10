from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status, serializers

from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer
from config.openapi import ProblemSchema

from users.serializers.register import RegisterSerializer


@extend_schema(
    summary="Créer un nouveau compte utilisateur",
    description=(
        "Valide les informations fournies (email, mot de passe, données personnelles) "
        "et crée un compte si toutes les règles sont respectées. "
        "Retourne l'ID et l'email du nouvel utilisateur en cas de succès. "
        "En cas d'erreur, renvoie un format `problem+json` avec un code stable et, "
        "le cas échéant, des détails par champ pour permettre une traduction côté client."
    ),
    request=RegisterSerializer,
    responses={
        201: OpenApiResponse(
            description="Inscription réussie.",
            response=inline_serializer(
                name="RegisterSuccess",
                fields={
                    "id": serializers.IntegerField(),
                    "email": serializers.EmailField(),
                }
            )
        ),
        400: OpenApiResponse(description="Données invalides", response=ProblemSchema),
        401: OpenApiResponse(description="Non authentifié", response=ProblemSchema),
        403: OpenApiResponse(description="Interdit", response=ProblemSchema),
        404: OpenApiResponse(description="Introuvable", response=ProblemSchema),
        429: OpenApiResponse(description="Trop de requêtes", response=ProblemSchema),
    },
    tags=["Utilisateurs"],
)
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Retour minimal "API-friendly"
        return Response(
            {"id": user.id, "email": user.email},
            status=status.HTTP_201_CREATED
        )
