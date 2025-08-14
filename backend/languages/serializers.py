# backend/languages/serializers.py
from rest_framework import serializers
from .models import Language

class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ["code", "label_fr", "label_en", "label_nl", "is_active", "sort_order"]
