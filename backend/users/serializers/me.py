from rest_framework import serializers
from rest_framework.reverse import reverse
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample, extend_schema_field

from users.models import User


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            name="Profil complet",
            value={
                "id": 1,
                "email": "jaber@conversa.be",
                "first_name": "Jaber",
                "last_name": "Bo",
                "bio": "Amoureux des langues et des rencontres culturelles",
                "language_native": "fr",
                "languages_spoken": ["en", "ar"],
                "date_joined": "2025-08-06T09:15:00Z",
                "is_profile_public": True,
                "links": {
                    "self": "/api/users/me/",
                    "update": "/api/users/me/",
                    "delete": "/api/users/me/",
                    "export": "/api/users/me/export/"
                }
            },
            response_only=True
        )
    ]
)
class UserMeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(help_text="Identifiant unique de l’utilisateur.")
    email = serializers.EmailField(help_text="Adresse e-mail utilisée pour se connecter.")
    first_name = serializers.CharField(help_text="Prénom visible dans le profil.")
    last_name = serializers.CharField(help_text="Nom visible dans le profil.")
    bio = serializers.CharField(help_text="Présentation personnelle de l’utilisateur.", allow_blank=True)
    language_native = serializers.CharField(help_text="Langue maternelle principale.")
    languages_spoken = serializers.ListField(
        child=serializers.CharField(),
        help_text="Liste des langues supplémentaires que l’utilisateur parle."
    )
    date_joined = serializers.DateTimeField(help_text="Date de création du compte.")
    is_profile_public = serializers.BooleanField(help_text="Indique si le profil est visible publiquement.")
    links = serializers.SerializerMethodField(help_text="Liens HATEOAS vers les actions sur le profil.")

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name",
            "bio", "language_native", "languages_spoken",
            "date_joined", "is_profile_public", "links"
        ]
        read_only_fields = ["id", "email", "date_joined"]

    @extend_schema_field(serializers.DictField())
    def get_links(self, obj):
        request = self.context.get("request")
        return {
            "self": reverse("user-me", request=request),
            "update": reverse("user-me", request=request),
            "delete": reverse("user-me", request=request),
            "export": reverse("user-export", request=request),
        }


class UserMeUpdateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(read_only=True, help_text="Adresse e-mail (non modifiable).")
    first_name = serializers.CharField(help_text="Prénom à afficher dans le profil.")
    last_name = serializers.CharField(help_text="Nom à afficher dans le profil.")
    bio = serializers.CharField(
        help_text="Texte libre pour se présenter.",
        allow_blank=True,
        required=False
    )
    languages_spoken = serializers.ListField(
        child=serializers.CharField(),
        help_text="Liste mise à jour des langues parlées par l’utilisateur."
    )
    is_profile_public = serializers.BooleanField(help_text="Indique si le profil est visible publiquement.")

    class Meta:
        model = User
        fields = [
            "email", "first_name", "last_name",
            "bio", "languages_spoken", "is_profile_public"
        ]
