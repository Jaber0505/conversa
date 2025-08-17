from django.contrib.auth import authenticate, get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken

from drf_spectacular.utils import extend_schema, OpenApiResponse

from .serializers import RegisterSerializer, UserSerializer
from .models import User
from common.mixins import HateoasOptionsMixin
from common.metadata import HateoasMetadata


User = get_user_model()


@extend_schema(
    tags=["Auth"],
    request=RegisterSerializer,
    responses={
        201: OpenApiResponse(response=UserSerializer, description="Utilisateur créé + tokens renvoyés"),
        400: OpenApiResponse(description="Données invalides"),
    },
)
class RegisterView(HateoasOptionsMixin, generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    metadata_class = HateoasMetadata

    extra_hateoas = {"related": {"login": "/api/v1/auth/login/", "me": "/api/v1/auth/me/"}}

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        data = serializer.data
        return Response(
            {**data, "refresh": str(refresh), "access": str(refresh.access_token)},
            status=status.HTTP_201_CREATED,
        )


# LOGIN → email + password → tokens
@extend_schema(
    tags=["Auth"],
    request={"application/json": {"email": "string", "password": "string"}},
    responses={
        200: OpenApiResponse(description="Connexion réussie + tokens renvoyés"),
        401: OpenApiResponse(description="Identifiants invalides"),
    },
)
class EmailLoginView(HateoasOptionsMixin, APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    metadata_class = HateoasMetadata

    extra_hateoas = {"related": {"register": "/api/v1/auth/register/", "refresh": "/api/v1/auth/refresh/"}}

    def post(self, request, *args, **kwargs):
        email = (request.data.get("email") or "").strip()
        password = request.data.get("password") or ""
        user = authenticate(request, username=email, password=password)
        if not user:
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
        refresh = RefreshToken.for_user(user)
        return Response({"refresh": str(refresh), "access": str(refresh.access_token)}, status=200)


# REFRESH → rotation + blacklist (activée en settings)
@extend_schema(
    tags=["Auth"],
    request={"application/json": {"refresh": "string"}},
    responses={
        200: OpenApiResponse(description="Access token renouvelé"),
        401: OpenApiResponse(description="Refresh expiré ou invalide"),
    },
)
class RefreshView(HateoasOptionsMixin, TokenRefreshView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    metadata_class = HateoasMetadata

    extra_hateoas = {"related": {"login": "/api/v1/auth/login/"}}


# LOGOUT → invalide refresh + revoke access
@extend_schema(
    tags=["Auth"],
    request={"application/json": {"refresh": "string"}},
    responses={
        204: OpenApiResponse(description="Déconnexion réussie"),
        400: OpenApiResponse(description="Refresh token manquant ou invalide"),
    },
)
class LogoutView(HateoasOptionsMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]
    metadata_class = HateoasMetadata

    extra_hateoas = {"related": {"login": "/api/v1/auth/login/"}}

    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"detail": "Refresh token required."}, status=status.HTTP_400_BAD_REQUEST)

        # 1) Blacklist refresh
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            return Response({"detail": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)

        # 2) Révoque access courant (denylist)
        try:
            from rest_framework_simplejwt.tokens import AccessToken
            from .models import RevokedAccessToken

            raw_access = str(request.auth)
            jti = AccessToken(raw_access)["jti"]
            RevokedAccessToken.objects.get_or_create(jti=jti)
        except Exception:
            pass

        return Response(status=status.HTTP_204_NO_CONTENT)


# ME → profil courant
@extend_schema(
    tags=["Auth"],
    responses={
        200: UserSerializer,   # => inclut is_staff/is_superuser/is_active
        401: OpenApiResponse(description="Non authentifié"),
    },
)
class MeView(HateoasOptionsMixin, generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    metadata_class = HateoasMetadata

    extra_hateoas = {"related": {"logout": "/api/v1/auth/logout/"}}

    def get_object(self):
        return self.request.user