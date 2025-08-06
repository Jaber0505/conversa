from rest_framework import serializers
from users.models import User

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            name="Profil public d’un utilisateur",
            value={
                "id": 12,
                "first_name": "Anna",
                "last_name": "Dubois",
                "age": 30,
                "language_native": "fr",
                "languages_spoken": ["en", "nl"],
                "bio": "Curieuse de découvrir de nouvelles cultures.",
            },
            summary="Exemple de réponse publique",
            response_only=True,
        )
    ]
)
class PublicUserSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour afficher les informations publiques d'un utilisateur,
    visible uniquement si son profil est marqué comme public.
    Aucun champ sensible ou contractuel n’est exposé.
    """
    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "age",
            "language_native",
            "languages_spoken",
            "bio",
        ]
        read_only_fields = fields
