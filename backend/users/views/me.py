from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from users.serializers import UserMeSerializer, UserMeUpdateSerializer
from users.permissions.base import IsSelf, IsAuthenticatedAndActive
from drf_spectacular.utils import extend_schema, OpenApiResponse

@extend_schema(
    summary="Consulter, modifier ou supprimer son propre profil",
    description=(
        "Permet à l'utilisateur connecté de consulter (`GET`), modifier (`PATCH`) ou supprimer (`DELETE`) son propre profil. "
        "L'accès est strictement limité à l'utilisateur lui-même grâce aux permissions `IsAuthenticatedAndActive` et `IsSelf`."
    ),
    tags=["Utilisateurs"],
    responses={
        200: UserMeSerializer,
        204: OpenApiResponse(description="Profil supprimé avec succès."),
        400: OpenApiResponse(description="Données invalides lors de la modification."),
        403: OpenApiResponse(description="Accès refusé."),
    },
)
class MeView(APIView):
    permission_classes = [IsAuthenticatedAndActive, IsSelf]

    def get(self, request):
        self.check_object_permissions(request, request.user)
        serializer = UserMeSerializer(request.user, context={"request": request})
        return Response(serializer.data)

    @extend_schema(request=UserMeUpdateSerializer)
    def patch(self, request):
        self.check_object_permissions(request, request.user)
        serializer = UserMeUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Profil mis à jour."})

    def delete(self, request):
        self.check_object_permissions(request, request.user)
        request.user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
