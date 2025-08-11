# languages/serializers/language.py
from rest_framework import serializers
from languages.models import Language

class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ("code", "names", "is_active", "sort_order", "created_at", "updated_at")

class LanguageOptionSerializer(serializers.ModelSerializer):
    label = serializers.SerializerMethodField()

    class Meta:
        model = Language
        fields = ("code", "label")

    def get_label(self, obj: Language) -> str:
        req = self.context.get("request")
        locale = (req.query_params.get("locale") if req else None) or "fr"
        return obj.names.get(locale) or obj.names.get("fr") or obj.code
