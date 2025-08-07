from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from drf_spectacular.utils import extend_schema
from users.permissions import IsAuthenticatedAndActive
from users.throttles import LoginThrottle

@extend_schema(
    summary="Authentification via JWT",
    description="""
        Aucune information ne sera divulguée sur l’existence du compte.
        Limite : `5 tentatives par minute` par IP.

        Réponse :
        - `200 OK` : authentification réussie, tokens retournés
        - `401 Unauthorized` : identifiants invalides
        - `429 Too Many Requests` : trop de tentatives, throttling actif
    """,
    tags=["Authentification"],
    request={
        "application/json": {
            "email": "user@example.com",
            "password": "MotDePasse123"
        }
    },
    responses={
        200: {
            "access": "access_token",
            "refresh": "refresh_token"
        },
        401: {"message": "Identifiants invalides"},
        429: {"message": "Trop de tentatives, réessaye plus tard."}
    }
)
class SpectacularTokenObtainPairView(TokenObtainPairView):
    throttle_classes = [LoginThrottle]

@extend_schema(exclude=True)
class SpectacularTokenRefreshView(TokenRefreshView):
    """Rafraîchir un token d’accès JWT"""
    pass


@extend_schema(
    summary="Ping d'authentification",
    description="""
        Permet de vérifier la validité d’un token d’authentification JWT.  
        Cette route utilise la méthode `HEAD` et ne retourne aucun contenu.

        Réponse :
        - 200 OK : authentifié
        - 401 Unauthorized : token invalide ou expiré
    """,
    tags=["Authentification"],
    responses={
        200: None,
        401: None
    }
)
class PingAuthView(APIView):
    permission_classes = [IsAuthenticatedAndActive]

    def head(self, request):
        return Response(status=status.HTTP_200_OK)

    def get(self, request):
        return Response(status=status.HTTP_200_OK)


@extend_schema(
    summary="Déconnexion (invalider le refresh token)",
    description="""
        Permet de se déconnecter en invalidant le `refresh token` JWT.  

        - Si le token est valide, il est mis sur liste noire.
        - Sinon, une réponse 400 est retournée.
    """,
    tags=["Authentification"],
    request={"application/json": {"refresh": "string"}},
    responses={
        205: None,
        400: {"message": "Invalid refresh token"}
    }
)
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)
