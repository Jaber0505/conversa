# backend/payments/serializers.py
from rest_framework import serializers

class CreateIntentSerializer(serializers.Serializer):
    booking = serializers.IntegerField(min_value=1)
