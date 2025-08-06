from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status

from users.serializers import RegisterSerializer
from drf_spectacular.utils import extend_schema, OpenApiResponse


@extend_schema(
    summary="Créer un compte utilisateur",
    description=(
        "Permet à un nouvel utilisateur de s'inscrire en fournissant une adresse e-mail, un mot de passe "
        "et les autres informations obligatoires. Renvoie un message de confirmation si l'inscription réussit."
    ),
    request=RegisterSerializer,
    responses={
        201: OpenApiResponse(description="Inscription réussie."),
        400: OpenApiResponse(description="Données invalides (email déjà utilisé, etc.)"),
    },
    tags=["Utilisateurs"],
)
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Inscription réussie."}, status=status.HTTP_201_CREATED)
