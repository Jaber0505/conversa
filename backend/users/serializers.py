"""User serializers for API endpoints."""
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from languages.models import Language
from common.constants import (
    MINIMUM_USER_AGE,
    MIN_USER_PASSWORD_LENGTH,
    MAX_USER_BIO_LENGTH,
    REQUIRED_NATIVE_LANGUAGES,
    REQUIRED_TARGET_LANGUAGES,
)

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    """Login request body."""

    email = serializers.EmailField(help_text="User email")
    password = serializers.CharField(
        write_only=True,
        help_text="User password",
        style={"input_type": "password"},
    )


class UserSerializer(serializers.ModelSerializer):
    """
    User read serializer.

    Returns complete user profile including languages and account status.
    """

    native_langs = serializers.SlugRelatedField(
        slug_field="code", many=True, read_only=True
    )
    target_langs = serializers.SlugRelatedField(
        slug_field="code", many=True, read_only=True
    )

    is_staff = serializers.BooleanField(read_only=True)
    is_superuser = serializers.BooleanField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "age",
            "bio",
            "avatar",
            "address",
            "city",
            "country",
            "latitude",
            "longitude",
            "native_langs",
            "target_langs",
            "is_staff",
            "is_superuser",
            "is_active",
            "date_joined",
        ]


class RegisterSerializer(serializers.ModelSerializer):
    """
    User registration serializer.

    Validates user input and creates new user account with language preferences.
    """

    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())],
        help_text="Unique email address",
    )
    password = serializers.CharField(
        write_only=True,
        min_length=MIN_USER_PASSWORD_LENGTH,
        help_text=f"Password (minimum {MIN_USER_PASSWORD_LENGTH} characters)",
    )
    first_name = serializers.CharField(help_text="First name")
    last_name = serializers.CharField(help_text="Last name")
    age = serializers.IntegerField(
        min_value=MINIMUM_USER_AGE, help_text=f"Age (minimum {MINIMUM_USER_AGE})"
    )

    consent_given = serializers.BooleanField(
        required=True, help_text="Must be true to create account"
    )

    native_langs = serializers.SlugRelatedField(
        slug_field="code",
        queryset=Language.objects.filter(is_active=True),
        many=True,
        help_text=f"Native languages (ISO codes, e.g., fr)",
    )
    target_langs = serializers.SlugRelatedField(
        slug_field="code",
        queryset=Language.objects.filter(is_active=True),
        many=True,
        help_text=f"Target languages (ISO codes, e.g., en)",
    )

    bio = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=MAX_USER_BIO_LENGTH,
        help_text=f"Biography (max {MAX_USER_BIO_LENGTH} characters)",
    )
    avatar = serializers.URLField(
        required=False, allow_blank=True, help_text="Avatar image URL"
    )
    address = serializers.CharField(
        required=False, allow_blank=True, max_length=255, help_text="Street address"
    )
    city = serializers.CharField(
        required=False, allow_blank=True, max_length=100, help_text="City"
    )
    country = serializers.CharField(
        required=False, allow_blank=True, max_length=100, help_text="Country code"
    )
    latitude = serializers.DecimalField(
        required=False,
        allow_null=True,
        max_digits=9,
        decimal_places=6,
        help_text="Latitude",
    )
    longitude = serializers.DecimalField(
        required=False,
        allow_null=True,
        max_digits=9,
        decimal_places=6,
        help_text="Longitude",
    )

    class Meta:
        model = User
        fields = [
            "email",
            "password",
            "first_name",
            "last_name",
            "age",
            "bio",
            "avatar",
            "address",
            "city",
            "country",
            "latitude",
            "longitude",
            "native_langs",
            "target_langs",
            "consent_given",
        ]

    def validate(self, attrs):
        """Validate registration data."""
        if not attrs.get("native_langs"):
            raise serializers.ValidationError(
                {"native_langs": "At least one native language is required."}
            )

        if not attrs.get("target_langs"):
            raise serializers.ValidationError(
                {"target_langs": "At least one target language is required."}
            )

        if attrs.get("consent_given") is not True:
            raise serializers.ValidationError(
                {"consent_given": "Consent is required to create an account."}
            )

        return attrs

    def create(self, validated_data):
        """Create user using UserService."""
        from .services import UserService

        native = validated_data.pop("native_langs", [])
        target = validated_data.pop("target_langs", [])
        password = validated_data.pop("password")
        consent = validated_data.pop("consent_given", False)

        user = UserService.create_user(
            password=password,
            native_langs=native,
            target_langs=target,
            consent_given=consent,
            **validated_data,
        )

        return user

    def to_representation(self, instance):
        """Return full user profile."""
        return UserSerializer(instance).data
