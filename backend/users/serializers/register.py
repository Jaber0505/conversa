from rest_framework import serializers
from users.models import User
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            name="Exemple d’inscription",
            value={
                "email": "alice@example.com",
                "password": "MotDePasse123",
                "first_name": "Alice",
                "last_name": "Martin",
                "age": 22,
                "language_native": "fr",
                "languages_spoken": ["en", "es"],
                "bio": "J’adore les langues",
                "consent_given": True,
            },
            request_only=True,
        ),
    ]
)
class RegisterSerializer(serializers.ModelSerializer):
    """
    Sérialiseur utilisé lors de l'inscription d'un nouvel utilisateur.

    - Le mot de passe est écrit uniquement (`write_only`) et doit faire au moins 8 caractères.
    - L'âge doit être ≥ 18.
    - Le consentement (`consent_given`) est requis pour respecter le RGPD.
    - Utilise `create_user()` pour le hash automatique du mot de passe.
    """

    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = (
            "email", "password", "first_name", "last_name", "age", "bio",
            "language_native", "languages_spoken", "consent_given"
        )

    def validate_age(self, value):
        if value < 18:
            raise serializers.ValidationError(
                "Vous devez avoir au moins 18 ans pour vous inscrire."
            )
        return value

    def validate_consent_given(self, value):
        if not value:
            raise serializers.ValidationError(
                "Le consentement est requis pour créer un compte."
            )
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        return user
