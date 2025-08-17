from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from languages.models import Language

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    # Relations en lecture
    native_langs = serializers.SlugRelatedField(slug_field="code", many=True, read_only=True)
    target_langs = serializers.SlugRelatedField(slug_field="code", many=True, read_only=True)

    # Flags d’admin/état pour visibilité côté client
    is_staff = serializers.BooleanField(read_only=True)
    is_superuser = serializers.BooleanField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name", "age",
            "bio", "avatar",
            "address", "city", "country", "latitude", "longitude",
            "native_langs", "target_langs",
            "is_staff", "is_superuser", "is_active",
            "date_joined",
        ]


MeSerializer = UserSerializer


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())],
        help_text="Adresse email unique"
    )
    password = serializers.CharField(write_only=True, min_length=9, help_text="Mot de passe")
    first_name = serializers.CharField(help_text="Prénom")
    last_name = serializers.CharField(help_text="Nom")
    age = serializers.IntegerField(min_value=18, help_text="Âge (≥18)")

    consent_given = serializers.BooleanField(required=True, help_text="Doit être vrai pour créer le compte")

    native_langs = serializers.SlugRelatedField(
        slug_field="code",
        queryset=Language.objects.filter(is_active=True),
        many=True,
        help_text="Langues natives (codes ISO, ex: fr)"
    )
    target_langs = serializers.SlugRelatedField(
        slug_field="code",
        queryset=Language.objects.filter(is_active=True),
        many=True,
        help_text="Langues cibles (codes ISO, ex: en)"
    )

    bio = serializers.CharField(required=False, allow_blank=True, max_length=500, help_text="Bio (≤500)")
    avatar = serializers.URLField(required=False, allow_blank=True, help_text="URL avatar")
    address = serializers.CharField(required=False, allow_blank=True, max_length=255, help_text="Adresse")
    city = serializers.CharField(required=False, allow_blank=True, max_length=100, help_text="Ville")
    country = serializers.CharField(required=False, allow_blank=True, max_length=100, help_text="Pays")
    latitude = serializers.DecimalField(required=False, allow_null=True, max_digits=9, decimal_places=6, help_text="Latitude")
    longitude = serializers.DecimalField(required=False, allow_null=True, max_digits=9, decimal_places=6, help_text="Longitude")

    class Meta:
        model = User
        fields = [
            "email", "password", "first_name", "last_name", "age",
            "bio", "avatar", "address", "city", "country", "latitude", "longitude",
            "native_langs", "target_langs",
            "consent_given",
        ]

    def validate(self, attrs):
        if not attrs.get("native_langs"):
            raise serializers.ValidationError({"native_langs": "Au moins une langue connue est requise."})
        if not attrs.get("target_langs"):
            raise serializers.ValidationError({"target_langs": "Au moins une langue cible est requise."})
        if attrs.get("consent_given") is not True:
            raise serializers.ValidationError({"consent_given": "Le consentement est obligatoire."})
        return attrs

    def create(self, validated_data):
        native = validated_data.pop("native_langs", [])
        target = validated_data.pop("target_langs", [])
        password = validated_data.pop("password")
        consent = validated_data.pop("consent_given", False)

        validated_data["email"] = (validated_data.get("email") or "").strip()

        user = User.objects.create(
            is_active=True,
            consent_given=bool(consent),
            consent_given_at=timezone.now() if consent else None,
            **validated_data
        )
        user.set_password(password)
        user.save()
        user.native_langs.set(native)
        user.target_langs.set(target)
        return user

    def to_representation(self, instance):
        # Retourne le profil complet (incluant is_staff/is_superuser/is_active)
        return UserSerializer(instance).data
