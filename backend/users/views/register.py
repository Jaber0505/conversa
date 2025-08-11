# users/views/register.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status, serializers

from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer
from config.openapi import ProblemSchema

from users.serializers.register import RegisterSerializer
from users.views.auth import _issue_tokens_for_user


@extend_schema(
    auth=[],
    summary="Créer un nouveau compte utilisateur",
    description=(
        "Inscription par email/mot de passe, avec choix de la langue maternelle "
        "et des langues connues / à apprendre (codes ISO). "
        "En cas de succès, l’utilisateur est automatiquement connecté (JWT)."
    ),
    request=RegisterSerializer,
    responses={
        201: OpenApiResponse(
            description="Inscription réussie",
            response=inline_serializer(
                name="RegisterSuccess",
                fields={
                    "id": serializers.IntegerField(),
                    "email": serializers.EmailField(),
                    "access": serializers.CharField(),
                    "refresh": serializers.CharField(),
                }
            )
        ),
        400: OpenApiResponse(description="Données invalides", response=ProblemSchema),
        401: OpenApiResponse(description="Non authentifié", response=ProblemSchema),
        403: OpenApiResponse(description="Interdit", response=ProblemSchema),
        404: OpenApiResponse(description="Introuvable", response=ProblemSchema),
        429: OpenApiResponse(description="Trop de requêtes", response=ProblemSchema),
    },
    tags=["Utilisateurs"],
)
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        s = RegisterSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = s.save()

        tokens = _issue_tokens_for_user(user)
        return Response(
            {"id": user.id, "email": user.email, **tokens},
            status=status.HTTP_201_CREATED
        )
