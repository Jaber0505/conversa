from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample

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
                "bio": "Curieuse de découvrir de nouvelles cultures."
            },
            summary="Exemple de réponse publique",
            response_only=True,
        )
    ]
)
class PublicUserSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(
        help_text="Identifiant unique de l’utilisateur."
    )
    first_name = serializers.CharField(
        help_text="Prénom visible publiquement."
    )
    last_name = serializers.CharField(
        help_text="Nom visible publiquement."
    )
    age = serializers.IntegerField(
        read_only=True,
        help_text="Âge de l’utilisateur affiché sur le profil public (calculé à partir de la date de naissance)."
    )
    language_native = serializers.CharField(
        help_text="Langue maternelle de l’utilisateur."
    )
    languages_spoken = serializers.ListField(
        child=serializers.CharField(),
        help_text="Langues supplémentaires que l’utilisateur parle."
    )
    bio = serializers.CharField(
        help_text="Présentation publique de l’utilisateur.",
        allow_blank=True
    )

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
