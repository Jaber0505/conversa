from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status

from users.serializers import RegisterSerializer
from drf_spectacular.utils import extend_schema, OpenApiResponse

@extend_schema(
    summary="Créer un compte utilisateur",
    description="""
        Ce endpoint permet à un nouvel utilisateur de s’inscrire sur la plateforme Conversa.

        Il est accessible à tous (`AllowAny`), sans authentification préalable.  
        L’utilisateur doit fournir les champs requis : email, mot de passe, prénom, etc. (selon le serializer).

        Si les données sont valides, un nouveau compte est créé et une réponse `201 Created` est renvoyée.

        En cas d'erreur (ex : email déjà utilisé), une réponse `400 Bad Request` est retournée avec les détails.
    """,
    request=RegisterSerializer,
    responses={
        201: OpenApiResponse(description="Inscription réussie."),
        400: OpenApiResponse(description="Données invalides (email déjà utilisé, etc.)"),
    },
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
