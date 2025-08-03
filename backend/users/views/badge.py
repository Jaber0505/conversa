from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from users.serializers.badge import UserBadgeSerializer


@extend_schema(
    responses=UserBadgeSerializer(many=True),
    description="Retourne la liste des badges de l'utilisateur connecté."
)
class UserBadgesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        badges = request.user.badges.all()
        serializer = UserBadgeSerializer(badges, many=True)
        return Response(serializer.data)
