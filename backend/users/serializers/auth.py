from rest_framework import serializers

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(help_text="Adresse email de l'utilisateur")
    password = serializers.CharField(help_text="Mot de passe")


class TokenRefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField(help_text="Token refresh JWT")
