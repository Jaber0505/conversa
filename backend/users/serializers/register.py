from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from datetime import date
from users.models import User

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    birth_date = serializers.DateField()
    bio = serializers.CharField(allow_blank=True, required=False)
    language_native = serializers.CharField()
    languages_spoken = serializers.ListField(child=serializers.CharField())
    consent_given = serializers.BooleanField()

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
            # message libre, mais surtout un CODE stable
            raise serializers.ValidationError("Age must be >= 18", code="AGE_MIN")
        return value

    def validate_consent_given(self, value):
        if not value:
            raise serializers.ValidationError("Consent required", code="CONSENT_REQUIRED")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        return user
