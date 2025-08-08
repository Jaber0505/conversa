from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from drf_spectacular.utils import extend_schema, OpenApiResponse
from drf_spectacular.openapi import AutoSchema
from users.permissions.base import IsAuthenticatedAndActive

# --- Serializer pour Logout (Swagger friendly) ---
class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(help_text="Refresh token JWT à invalider.")

# --- Exclure les vues JWT natives de Swagger ---
@extend_schema(exclude=True)
class SpectacularTokenObtainPairView(TokenObtainPairView):
    """Obtenir tokens JWT (access + refresh)"""
    pass

@extend_schema(exclude=True)
class SpectacularTokenRefreshView(TokenRefreshView):
    """Rafraîchir un token JWT"""
    pass

# --- Ping Auth compatible Swagger ---
@extend_schema(
    summary="Ping d'authentification",
    description=(
        "Vérifie la validité du token JWT.\n\n"
        "- 200 OK si authentifié et actif\n"
        "- 401 Unauthorized sinon"
    ),
    tags=["Authentification"],
    methods=["HEAD"],
    responses={200: None, 401: None},
)
class PingAuthView(APIView):
    permission_classes = [IsAuthenticatedAndActive]

    def head(self, request):
        return Response(status=status.HTTP_200_OK)

# --- Logout avec schéma Swagger clair ---
@extend_schema(
    summary="Déconnexion (invalidation du refresh token)",
    description=(
        "Permet de se déconnecter en invalidant le refresh token JWT.\n"
        "L'utilisateur doit être authentifié et fournir le token à invalider.\n"
        "- 205 Reset Content si succès\n"
        "- 400 Bad Request sinon"
    ),
    tags=["Authentification"],
    request=LogoutSerializer,
    responses={
        205: OpenApiResponse(description="Token invalidé avec succès."),
        400: OpenApiResponse(description="Token invalide ou manquant."),
    },
)
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    schema = AutoSchema()

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            token = RefreshToken(serializer.validated_data["refresh"])
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)
