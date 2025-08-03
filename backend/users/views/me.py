from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from drf_spectacular.utils import extend_schema

from users.serializers.user import UserSerializer, UserUpdateSerializer

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        methods=["GET"],
        responses=UserSerializer,
        description="Returns complete information about the logged-in user."
    )
    @extend_schema(
        methods=["PATCH"],
        request=UserUpdateSerializer,
        responses=UserSerializer,
        description="Partially updates the user profile."
    )
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            user = serializer.save()
            return Response(UserSerializer(user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
