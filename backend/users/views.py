from django.contrib.auth import authenticate
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RegisterSerializer, UserSerializer
from .models import User

# REGISTER → crée user + renvoie profil + tokens
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []  # public

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        data = serializer.data  # UserSerializer
        return Response({**data, "refresh": str(refresh), "access": str(refresh.access_token)},
                        status=status.HTTP_201_CREATED)

# LOGIN (simple, sans confirmation d'email) → email+password
class EmailLoginView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []  # public

    def post(self, request, *args, **kwargs):
        email = (request.data.get("email") or "").strip()
        password = request.data.get("password") or ""
        user = authenticate(request, username=email, password=password)
        if not user:
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
        refresh = RefreshToken.for_user(user)
        return Response({"refresh": str(refresh), "access": str(refresh.access_token)}, status=200)

# REFRESH (rotation + blacklist si activé côté settings)
class RefreshView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []  # public

# LOGOUT → blacklist du refresh + revoke de l'access courant (denylist)
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"detail": "Refresh token required."}, status=status.HTTP_400_BAD_REQUEST)
        # 1) Blacklist du refresh
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            return Response({"detail": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)
        # 2) Révocation de l'access (denylist) → /me renvoie 401 immédiatement
        try:
            from rest_framework_simplejwt.tokens import AccessToken
            from .models import RevokedAccessToken
            raw_access = str(request.auth)  # JWT de l'en-tête Bearer
            jti = AccessToken(raw_access)["jti"]
            RevokedAccessToken.objects.get_or_create(jti=jti)
        except Exception:
            pass
        return Response(status=status.HTTP_204_NO_CONTENT)

# ME → profil courant
class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_object(self):
        return self.request.user
