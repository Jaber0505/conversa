# backend/users/serializers.py
from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=9)
    class Meta:
        model = User
        fields = ["username", "email", "password"]
    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]
        read_only_fields = fields
