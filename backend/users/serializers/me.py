from rest_framework import serializers
from rest_framework.reverse import reverse
from users.models import User

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            name="Profil complet",
            value={
                "id": 1,
                "email": "jaber@conversa.be",
                "first_name": "Jaber",
                "last_name": "Boudouh",
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
    """
    Sérialiseur pour afficher les données personnelles de l'utilisateur connecté.
    Exclut les champs sensibles comme le mot de passe et les rôles internes.
    Fournit des liens HATEOAS pour les actions possibles.
    """
    links = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name",
            "bio", "language_native", "languages_spoken",
            "date_joined", "is_profile_public", "links"
        ]
        read_only_fields = ["id", "email", "date_joined"]

    def get_links(self, obj):
        request = self.context.get("request")
        return {
            "self": reverse("user-me", request=request),
            "update": reverse("user-me", request=request),
            "delete": reverse("user-me", request=request),
            "export": reverse("user-export", request=request),
        }


class UserMeUpdateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour mettre à jour le profil de l'utilisateur.
    Ne permet de modifier que certains champs définis.
    """
    class Meta:
        model = User
        fields = ["first_name", "last_name", "bio", "languages_spoken"]
