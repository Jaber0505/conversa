from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from drf_spectacular.types import OpenApiTypes

from users.throttles import PasswordResetThrottle

User = get_user_model()


@extend_schema(
    summary="Demander une réinitialisation de mot de passe",
    description="""
        Permet à un utilisateur de demander un lien de réinitialisation de mot de passe.
        Cette route est **limitée à 5 tentatives par heure** par IP pour éviter les abus.
    """,
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "format": "email",
                    "example": "alice@example.com"
                }
            },
            "required": ["email"]
        }
    },
    responses={
        200: OpenApiResponse(
            description="Lien de réinitialisation envoyé (si compte existant).",
            response=OpenApiTypes.OBJECT,
            examples=[
                OpenApiExample(
                    name="reset_email_sent",
                    value={
                        "detail": (
                            "Si cette adresse est enregistrée, un lien de réinitialisation "
                            "a été envoyé par email."
                        )
                    }
                )
            ]
        ),
        429: OpenApiResponse(
            description="Trop de tentatives. Attends avant de réessayer.",
            response=OpenApiTypes.OBJECT,
            examples=[
                OpenApiExample(
                    name="too_many_requests",
                    value={"detail": "Trop de tentatives. Réessaie dans une heure."}
                )
            ]
        ),
    },
    tags=["Utilisateurs"]
)
class RequestPasswordResetView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [PasswordResetThrottle]

    def post(self, request):
        email = request.data.get("email")
        user = User.objects.filter(email=email).first()

        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            reset_link = (
                f"{request.build_absolute_uri('/')}reset-password/confirm/"
                f"?uid={uid}&token={token}"
            )

            send_mail(
                subject="Réinitialisation de votre mot de passe",
                message=f"Voici votre lien : {reset_link}",
                from_email="no-reply@conversa.be",
                recipient_list=[email],
            )

        return Response(
            {"detail": "Si cet email est enregistré, un lien a été envoyé."},
            status=status.HTTP_200_OK
        )


@extend_schema(
    summary="Confirmer la réinitialisation de mot de passe",
    description="""
        Cette route permet à un utilisateur de finaliser la réinitialisation de son mot de passe.
        Le lien contient deux éléments indispensables :
        - le `uid` (identifiant encodé en base64),
        - le `token` (valide temporairement, généré par Django).
        En cas de succès, un nouveau mot de passe est défini.  
        En cas d’échec (lien expiré ou invalide), une erreur est retournée.
        Le mot de passe doit contenir au moins 8 caractères.
    """,
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "uid": {"type": "string", "example": "Mg"},
                "token": {"type": "string", "example": "1x2v8v-7eb83a4d7f251b63ebc"},
                "new_password": {"type": "string", "example": "MonNouveauMotDePasse123"}
            },
            "required": ["uid", "token", "new_password"]
        }
    },
    responses={
        200: OpenApiResponse(
            description="Mot de passe réinitialisé avec succès.",
            response=OpenApiTypes.OBJECT,
            examples=[
                OpenApiExample(
                    name="reset_success",
                    value={
                        "detail": (
                            "Votre mot de passe a été mis à jour. "
                            "Vous pouvez désormais vous connecter avec votre nouveau mot de passe."
                        )
                    }
                )
            ]
        ),
        400: OpenApiResponse(
            description="Lien invalide, expiré ou mot de passe incorrect.",
            response=OpenApiTypes.OBJECT,
            examples=[
                OpenApiExample(
                    name="token_invalid",
                    value={"detail": "Token invalide ou expiré."}
                ),
                OpenApiExample(
                    name="too_short",
                    value={"detail": "Le mot de passe doit contenir au moins 8 caractères."}
                ),
                OpenApiExample(
                    name="uid_invalid",
                    value={"detail": "Lien invalide."}
                ),
            ]
        )
    },
    tags=["Utilisateurs"]
)
class ConfirmPasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        uidb64 = request.data.get("uid")
        token = request.data.get("token")
        new_password = request.data.get("new_password")

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError):
            return Response({"detail": "Lien invalide."}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({"detail": "Token invalide ou expiré."}, status=status.HTTP_400_BAD_REQUEST)

        if len(new_password) < 8:
            return Response(
                {"detail": "Le mot de passe doit contenir au moins 8 caractères."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()

        return Response(
            {
                "detail": (
                    "Votre mot de passe a été mis à jour. "
                    "Vous pouvez désormais vous connecter avec votre nouveau mot de passe."
                )
            },
            status=status.HTTP_200_OK
        )
