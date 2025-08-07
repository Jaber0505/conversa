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
        Permet d'obtenir un `access_token` et un `refresh_token` en envoyant l'adresse email et le mot de passe.

        Aucune information ne sera fournie sur la validité ou l’existence du compte associé à l’email ou au mot de passe.  
        Que ce soit en cas d’échec ou de succès, la réponse reste neutre pour des raisons de **sécurité** et de **protection des données personnelles** (conformité RGPD).

        Limite de requêtes : `5 tentatives par minute` par IP.  
        Un dépassement entraînera une erreur `429 Too Many Requests`.

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

        - Si l’utilisateur est authentifié **et actif**, la réponse sera `200 OK`.
        - Si le token est manquant, expiré ou associé à un compte désactivé, la réponse sera `401 Unauthorized`.

        Ce endpoint est utile pour :
        - les **clients front-end** qui veulent vérifier l’état de session de manière silencieuse,
        - les **tests automatisés** pour valider l’authentification,
        - ou encore pour implémenter un **auto-refresh** côté client si `401` est détecté.

        - `HEAD` : recommandé côté front pour un check rapide et sans charge
        - `GET` : uniquement présent pour permettre l'affichage dans Swagger

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
        L'utilisateur doit être authentifié (`access token` requis), et fournir son `refresh token` dans le corps de la requête.

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
