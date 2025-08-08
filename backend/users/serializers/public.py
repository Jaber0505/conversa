from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample, extend_schema_field

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
    age = serializers.SerializerMethodField(
        help_text="Âge de l’utilisateur affiché sur le profil public (calculé automatiquement)."
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

    @extend_schema_field(serializers.IntegerField(help_text="Âge calculé automatiquement à partir de la date de naissance."))
    def get_age(self, obj) -> int:
        return obj.age
