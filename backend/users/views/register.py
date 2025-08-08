from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status

from users.serializers import RegisterSerializer
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

@extend_schema(
    summary="Créer un compte utilisateur",
    description="""
        Ce endpoint permet à un nouvel utilisateur de s’inscrire sur la plateforme Conversa.

        Il est accessible à tous (`AllowAny`), sans authentification préalable.  
        L’utilisateur doit fournir les champs requis : email, mot de passe, prénom, etc.

        Si les données sont valides, un nouveau compte est créé et une réponse `201 Created` est renvoyée.
    """,
    request=RegisterSerializer,
    responses={
        201: OpenApiResponse(description="Inscription réussie."),
        400: OpenApiResponse(description="Données invalides (email déjà utilisé, etc.)"),
    },
    examples=[
        OpenApiExample(
            name="Exemple d’inscription",
            summary="Exemple complet de payload d’inscription",
            value={
                "email": "alice@example.com",
                "password": "MotDePasse123",
                "first_name": "Alice",
                "last_name": "Martin",
                "birth_date": "2003-08-07",
                "bio": "J’adore les langues",
                "language_native": "fr",
                "languages_spoken": ["en", "es"],
                "consent_given": True
            },
            request_only=True,
        )
    ],
    tags=["Utilisateurs"]
)
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Inscription réussie."},
            status=status.HTTP_201_CREATED
        )
