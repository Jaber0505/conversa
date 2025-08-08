from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from datetime import date

from users.models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text="Mot de passe confidentiel (minimum 8 caractères)."
    )
    email = serializers.EmailField(
        help_text="Adresse email utilisée pour se connecter à la plateforme.",
        validators=[UniqueValidator(queryset=User.objects.all(), message="Un compte avec cet email existe déjà.")]
    )
    first_name = serializers.CharField(help_text="Prénom affiché publiquement sur le profil.")
    last_name = serializers.CharField(help_text="Nom de famille affiché publiquement sur le profil.")
    birth_date = serializers.DateField(help_text="Date de naissance (vous devez avoir au moins 18 ans).")
    bio = serializers.CharField(help_text="Texte libre pour vous présenter aux autres joueurs.",
                                 allow_blank=True, required=False)
    language_native = serializers.CharField(help_text="Langue maternelle principale.")
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
            "birth_date", "bio", "language_native", "languages_spoken", "consent_given"
        )

    def validate_birth_date(self, value):
        today = date.today()
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        if age < 18:
            raise serializers.ValidationError("Vous devez avoir au moins 18 ans pour vous inscrire.")
        return value

    def validate_consent_given(self, value):
        if not value:
            raise serializers.ValidationError("Le consentement est requis pour créer un compte.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        return user
