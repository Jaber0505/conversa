from rest_framework import serializers
from users.models import UserPreferences

class UserPreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreferences
        fields = ['receive_notifications', 'ui_language']
