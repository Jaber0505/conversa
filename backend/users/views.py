# backend/users/views.py
from rest_framework import generics, permissions
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .serializers import RegisterSerializer, MeSerializer

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]

class RefreshView(TokenRefreshView):
    permission_classes = [AllowAny]

class MeView(generics.RetrieveAPIView):
    serializer_class = MeSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_object(self):
        return self.request.user
