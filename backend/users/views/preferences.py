from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from drf_spectacular.utils import extend_schema

from users.serializers.preferences import UserPreferencesSerializer
from users.models import UserPreferences


@extend_schema(
    methods=["GET"],
    responses=UserPreferencesSerializer,
    description="Retourne les préférences de l'utilisateur connecté."
)
@extend_schema(
    methods=["PATCH"],
    request=UserPreferencesSerializer,
    responses=UserPreferencesSerializer,
    description="Met à jour partiellement les préférences utilisateur."
)
class UserPreferencesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        preferences, _ = UserPreferences.objects.get_or_create(user=request.user)
        serializer = UserPreferencesSerializer(preferences)
        return Response(serializer.data)

    def patch(self, request):
        preferences, _ = UserPreferences.objects.get_or_create(user=request.user)
        serializer = UserPreferencesSerializer(preferences, data=request.data, partial=True)
        if serializer.is_valid():
            updated = serializer.save()
            return Response(UserPreferencesSerializer(updated).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
