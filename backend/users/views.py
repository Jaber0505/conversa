# backend/users/views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RegisterSerializer, LoginSerializer, UserSerializer
from .models import User

# REGISTER → crée user + renvoie profil + tokens
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def create(self, request, *args, **kwargs):
        # Valider + créer
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Tokens
        refresh = RefreshToken.for_user(user)
        tokens = {"refresh": str(refresh), "access": str(refresh.access_token)}

        # Profil
        data = serializer.data  # UserSerializer via to_representation
        return Response({**data, **tokens}, status=status.HTTP_201_CREATED)

# LOGIN → SimpleJWT (email + password)
class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

# REFRESH → SimpleJWT
class RefreshView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

# LOGOUT → blacklist du refresh + revoke de l'access courant
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"detail": "Refresh token required."}, status=status.HTTP_400_BAD_REQUEST)

        # 1) Blacklist du refresh (SimpleJWT)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            return Response({"detail": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)

        # 2) Révocation de l'access envoyé dans Authorization
        from rest_framework_simplejwt.tokens import AccessToken
        from .models import RevokedAccessToken

        try:
            raw_access = str(request.auth)  # le JWT de l'en-tête Bearer
            jti = AccessToken(raw_access)["jti"]
            RevokedAccessToken.objects.get_or_create(jti=jti)
        except Exception:
            # Si pas d'access ou token illisible, on ignore
            pass

        return Response(status=status.HTTP_204_NO_CONTENT)
    
# ME → profil de l’utilisateur courant
class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_object(self):
        return self.request.user
