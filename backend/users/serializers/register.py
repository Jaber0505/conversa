from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from datetime import date

from users.models import User


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
        )
    ]
)
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text="Mot de passe confidentiel (minimum 8 caractères)."
    )
    email = serializers.EmailField(
        help_text="Adresse email utilisée pour se connecter à la plateforme."
    )
    first_name = serializers.CharField(
        help_text="Prénom affiché publiquement sur le profil."
    )
    last_name = serializers.CharField(
        help_text="Nom de famille affiché publiquement sur le profil."
    )
    age = serializers.IntegerField(
        help_text="Âge de l'utilisateur (minimum requis : 18 ans)."
    )
    bio = serializers.CharField(
        help_text="Texte libre pour vous présenter aux autres joueurs.",
        allow_blank=True,
        required=False
    )
    language_native = serializers.CharField(
        help_text="Langue maternelle principale."
    )
    languages_spoken = serializers.ListField(
        child=serializers.CharField(),
        help_text="Langues parlées en plus de la langue maternelle."
    )
    consent_given = serializers.BooleanField(
        help_text="Consentement explicite au traitement des données personnelles (RGPD)."
    )

    class Meta:
        model = User
        fields = (
            "email", "password", "first_name", "last_name",
            "age", "bio", "language_native", "languages_spoken", "consent_given"
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
        age = validated_data.pop("age")

        today = date.today()
        birth_date = date(today.year - age, today.month, today.day)

        validated_data["birth_date"] = birth_date

        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        return user
