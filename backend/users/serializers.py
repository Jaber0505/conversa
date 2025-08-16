from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from languages.models import Language

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    native_langs = serializers.SlugRelatedField(slug_field="code", many=True, read_only=True)
    target_langs = serializers.SlugRelatedField(slug_field="code", many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name", "age",
            "bio", "avatar",
            "address", "city", "country", "latitude", "longitude",
            "native_langs", "target_langs", "date_joined",
        ]

MeSerializer = UserSerializer

class RegisterSerializer(serializers.ModelSerializer):
    # Obligatoires
    email = serializers.EmailField(validators=[UniqueValidator(queryset=User.objects.all())])
    password = serializers.CharField(write_only=True, min_length=9)
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    age = serializers.IntegerField(min_value=18)

    # Langues via codes ISO (doivent exister en DB)
    native_langs = serializers.SlugRelatedField(
        slug_field="code", queryset=Language.objects.all(), many=True
    )
    target_langs = serializers.SlugRelatedField(
        slug_field="code", queryset=Language.objects.all(), many=True
    )

    # Optionnels
    bio = serializers.CharField(required=False, allow_blank=True, max_length=500)
    avatar = serializers.URLField(required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True, max_length=255)
    city = serializers.CharField(required=False, allow_blank=True, max_length=100)
    country = serializers.CharField(required=False, allow_blank=True, max_length=100)
    latitude = serializers.DecimalField(required=False, allow_null=True, max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(required=False, allow_null=True, max_digits=9, decimal_places=6)

    class Meta:
        model = User
        fields = [
            "email", "password", "first_name", "last_name", "age",
            "bio", "avatar", "address", "city", "country", "latitude", "longitude",
            "native_langs", "target_langs",
        ]

    def validate(self, attrs):
        if not attrs.get("native_langs"):
            raise serializers.ValidationError({"native_langs": "Au moins une langue connue est requise."})
        if not attrs.get("target_langs"):
            raise serializers.ValidationError({"target_langs": "Au moins une langue cible est requise."})
        return attrs

    def create(self, validated_data):
        # email propre + compte actif directement
        validated_data["email"] = (validated_data.get("email") or "").strip()
        native = validated_data.pop("native_langs", [])
        target = validated_data.pop("target_langs", [])
        password = validated_data.pop("password")

        user = User.objects.create(is_active=True, **validated_data)
        user.set_password(password)
        user.save()

        user.native_langs.set(native)
        user.target_langs.set(target)
        return user

    def to_representation(self, instance):
        return UserSerializer(instance).data
