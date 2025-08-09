from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.throttling import ScopedRateThrottle
from django.contrib.auth import authenticate

from rest_framework_simplejwt.tokens import RefreshToken
from users.serializers.auth import LoginSerializer, TokenRefreshSerializer
from users.permissions.base import IsAuthenticatedAndActive


class CustomTokenObtainPairView(APIView):
    schema = None
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"]
        )
        if user is None:
            return Response({"detail": "Identifiants invalides"}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }, status=status.HTTP_200_OK)
    
class CustomTokenRefreshView(APIView):
    schema = None
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TokenRefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            refresh = RefreshToken(serializer.validated_data['refresh'])
            access_token = str(refresh.access_token)
            return Response({"access": access_token}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"detail": "Token refresh invalide"}, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    schema = None
    permission_classes = [IsAuthenticatedAndActive]

    def post(self, request):
        serializer = TokenRefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            token = RefreshToken(serializer.validated_data["refresh"])
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class PingAuthView(APIView):
    schema = None
    permission_classes = [IsAuthenticatedAndActive]

    def head(self, request):
        return Response(status=status.HTTP_200_OK)

    def get(self, request):
        return Response(status=status.HTTP_200_OK)