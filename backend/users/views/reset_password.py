from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

User = get_user_model()

@extend_schema(
    summary="Demander une réinitialisation de mot de passe",
    description=(
        "Permet à un utilisateur de demander un lien de réinitialisation de mot de passe.\n"
        "Un email contenant un lien sécurisé sera envoyé si l'adresse est connue."
    ),
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
    responses={200: None},
    examples=[
        OpenApiExample(
            name="Réponse générique",
            value={"detail": "Si cet email est enregistré, un lien a été envoyé."},
            response_only=True
        )
    ]
)
class RequestPasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        user = User.objects.filter(email=email).first()

        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            reset_link = f"{request.build_absolute_uri('/')}reset-password/confirm/?uid={uid}&token={token}"

            send_mail(
                subject="Réinitialisation de votre mot de passe",
                message=f"Voici votre lien : {reset_link}",
                from_email="no-reply@conversa.be",
                recipient_list=[email],
            )

        # Ne jamais révéler si l’email est connu ou non
        return Response({"detail": "Si cet email est enregistré, un lien a été envoyé."}, status=200)

@extend_schema(
    summary="Confirmer la réinitialisation de mot de passe",
    description=(
        "Permet de réinitialiser le mot de passe en soumettant un nouveau mot de passe "
        "accompagné du `uid` et du `token` fournis dans le lien reçu par email."
    ),
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
        200: None,
        400: None
    },
    examples=[
        OpenApiExample(
            name="Réinitialisation réussie",
            value={"detail": "Mot de passe mis à jour avec succès."},
            response_only=True,
            status_codes=["200"]
        ),
        OpenApiExample(
            name="Lien ou token invalide",
            value={"detail": "Token invalide ou expiré."},
            response_only=True,
            status_codes=["400"]
        )
    ]
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
            return Response({"detail": "Lien invalide."}, status=400)

        if not default_token_generator.check_token(user, token):
            return Response({"detail": "Token invalide ou expiré."}, status=400)

        if len(new_password) < 8:
            return Response({"detail": "Le mot de passe doit contenir au moins 8 caractères."}, status=400)

        user.set_password(new_password)
        user.save()

        return Response({"detail": "Mot de passe mis à jour avec succès."})
