# users/serializers/register.py
from datetime import date
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from users.models import User
from languages.models import Language


class LanguageByCodeField(serializers.SlugRelatedField):
    """SlugRelatedField qui renvoie un code d'erreur stable si le code n'existe pas."""
    def to_internal_value(self, data):
        try:
            return super().to_internal_value(data)
        except serializers.ValidationError:
            raise serializers.ValidationError("Unknown language code", code="LANGUAGE_UNKNOWN")


class RegisterSerializer(serializers.ModelSerializer):
    # Identité & sécurité
    email = serializers.EmailField(validators=[UniqueValidator(queryset=User.objects.all())])
    password = serializers.CharField(write_only=True, min_length=8)

    # Profil
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    birth_date = serializers.DateField()
    bio = serializers.CharField(allow_blank=True, required=False)

    # Langues
    language_native = LanguageByCodeField(
        slug_field="code",
        source="native_language",
        queryset=Language.objects.filter(is_active=True),
        help_text="Code ISO de la langue maternelle (ex: 'fr')."
    )
    languages_spoken = LanguageByCodeField(
        slug_field="code",
        source="spoken_languages",
        queryset=Language.objects.filter(is_active=True),
        many=True,
        required=False,
        default=list,
        help_text="Codes ISO des langues supplémentaires connues (ex: ['en','nl'])."
    )
    languages_wanted = LanguageByCodeField(
        slug_field="code",
        source="wanted_languages",
        queryset=Language.objects.filter(is_active=True),
        many=True,
        required=False,
        default=list,
        help_text="Codes ISO des langues à apprendre (ex: ['es','de'])."
    )

    consent_given = serializers.BooleanField()

    class Meta:
        model = User
        fields = (
            "email", "password",
            "first_name", "last_name", "birth_date", "bio",
            "language_native", "languages_spoken", "languages_wanted",
            "consent_given",
        )

    # ---- Validations simples
    def validate_birth_date(self, value):
        today = date.today()
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        if age < 18:
            raise serializers.ValidationError("Age must be >= 18", code="AGE_MIN")
        return value

    def validate_consent_given(self, value):
        if not value:
            raise serializers.ValidationError("Consent required", code="CONSENT_REQUIRED")
        return value

    # ---- Nettoyage langues (exclure native des parlées + dédup)
    def validate(self, attrs):
        native = attrs.get("native_language")
        spoken = list(attrs.get("spoken_languages") or [])
        wanted = list(attrs.get("wanted_languages") or [])

        def dedup_keep_order(items):
            seen, out = set(), []
            for obj in items:
                pk = getattr(obj, "pk", obj)
                if pk in seen:
                    continue
                seen.add(pk)
                out.append(obj)
            return out

        # Exclure la native des parlées si présente
        if native:
            spoken = [l for l in spoken if l.pk != native.pk]

        attrs["spoken_languages"] = dedup_keep_order(spoken)
        attrs["wanted_languages"] = dedup_keep_order(wanted)
        return attrs

    # ---- Création
    def create(self, validated_data):
        password = validated_data.pop("password")
        spoken = validated_data.pop("spoken_languages", [])
        wanted = validated_data.pop("wanted_languages", [])

        user = User(**validated_data)
        user.set_password(password)
        user.save()

        if spoken:
            user.spoken_languages.set(spoken)
        if wanted:
            user.wanted_languages.set(wanted)

        return user
