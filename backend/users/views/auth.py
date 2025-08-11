# users/views/auth.py
from django.contrib.auth import authenticate
from rest_framework import status, serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer
from config.openapi import ProblemSchema

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer as SJWTTokenRefreshSerializer

from users.serializers.auth import LoginSerializer, TokenRefreshSerializer
from users.models import User


def _issue_tokens_for_user(user: User) -> dict:
    """
    Crée un couple (refresh/access) et ajoute quelques claims utiles.
    """
    refresh = RefreshToken.for_user(user)
    # Claims optionnels (facultatifs mais pratiques côté front / future révocation)
    refresh["uid"] = user.pk
    refresh["email"] = user.email
    refresh["jk"] = str(user.jwt_key)

    access = refresh.access_token
    access["uid"] = user.pk
    access["email"] = user.email
    access["jk"] = str(user.jwt_key)

    return {"refresh": str(refresh), "access": str(access)}


@extend_schema(
    auth=[],
    summary="Se connecter (email + mot de passe)",
    description="Authentifie l’utilisateur et renvoie un couple de jetons JWT (access/refresh).",
    request=LoginSerializer,
    responses={
        200: OpenApiResponse(
            response=inline_serializer(
                name="LoginSuccess",
                fields={
                    "access": serializers.CharField(),
                    "refresh": serializers.CharField(),
                    "id": serializers.IntegerField(),
                    "email": serializers.EmailField(),
                },
            ),
            description="Connexion réussie",
        ),
        400: OpenApiResponse(description="Données invalides", response=ProblemSchema),
        401: OpenApiResponse(description="Non authentifié", response=ProblemSchema),
        403: OpenApiResponse(description="Interdit", response=ProblemSchema),
        429: OpenApiResponse(description="Trop de requêtes", response=ProblemSchema),
    },
    tags=["Auth"],
)
class CustomTokenObtainPairView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        s = LoginSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        email = s.validated_data["email"]
        password = s.validated_data["password"]

        # Django accepte email comme USERNAME_FIELD
        user = authenticate(request=request, email=email, password=password) or \
               authenticate(request=request, username=email, password=password)

        if not user:
            # On renvoie une ValidationError => format problem+json avec code stable
            raise serializers.ValidationError(
                {"email": serializers.ErrorDetail("Invalid email or password", code="LOGIN_FAILED")}
            )
        if not user.is_active:
            # 403 via le handler global
            raise serializers.ValidationError(
                {"email": serializers.ErrorDetail("User account disabled", code="USER_DISABLED")}
            )

        tokens = _issue_tokens_for_user(user)
        return Response(
            {"id": user.id, "email": user.email, **tokens},
            status=status.HTTP_200_OK,
        )


@extend_schema(
    auth=[],  # public dans la doc
    summary="Rafraîchir le token d’accès",
    description="Prend un refresh token valide et renvoie un nouveau token d’accès (et potentiellement un nouveau refresh si la rotation est activée).",
    request=TokenRefreshSerializer,  # notre simple schema {"refresh": "..."}
    responses={
        200: OpenApiResponse(
            response=inline_serializer(
                name="TokenRefreshSuccess",
                fields={
                    "access": serializers.CharField(),
                    # Si ROTATE_REFRESH_TOKENS=True alors SimpleJWT peut aussi renvoyer un refresh
                    "refresh": serializers.CharField(required=False),
                },
            ),
            description="Token rafraîchi",
        ),
        401: OpenApiResponse(description="Non authentifié", response=ProblemSchema),
        400: OpenApiResponse(description="Données invalides", response=ProblemSchema),
    },
    tags=["Auth"],
)
class CustomTokenRefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # On délègue à la serializer officielle SimpleJWT pour gérer rotation/blacklist
        serializer = SJWTTokenRefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


@extend_schema(
    summary="Se déconnecter (blacklist du refresh courant)",
    description="Invalide le refresh token courant (si fourni) en le plaçant en liste noire. Nécessite d’être authentifié.",
    request=inline_serializer(
        name="LogoutRequest",
        fields={"refresh": serializers.CharField(required=True)},
    ),
    responses={204: OpenApiResponse(description="Déconnexion réussie"),
               400: OpenApiResponse(description="Données invalides", response=ProblemSchema)},
    tags=["Auth"],
)
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh = request.data.get("refresh")
        if not refresh:
            raise serializers.ValidationError(
                {"refresh": serializers.ErrorDetail("Refresh token required", code="TOKEN_REQUIRED")}
            )

        try:
            token = RefreshToken(refresh)
            # Blacklist du refresh fourni
            token.blacklist()
        except Exception:
            # On garde un code stable
            raise serializers.ValidationError(
                {"refresh": serializers.ErrorDetail("Invalid refresh token", code="TOKEN_INVALID")}
            )

        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    summary="Ping authentifié",
    description="Vérifie que l’authentification JWT fonctionne.",
    responses={200: OpenApiResponse(
        response=inline_serializer(
            name="PingAuth",
            fields={"status": serializers.CharField(), "user_id": serializers.IntegerField(), "email": serializers.EmailField()},
        ),
        description="OK",
    )},
    tags=["Auth"],
)
class PingAuthView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"status": "ok", "user_id": request.user.id, "email": request.user.email})
