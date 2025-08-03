# users/serializers/user.py

from rest_framework import serializers
from users.models import User
from users.serializers.language import LanguageSerializer
from users.serializers.badge import UserBadgeSerializer
from users.serializers.preferences import UserPreferencesSerializer
from users.models import Language

class UserSerializer(serializers.ModelSerializer):
    native_language = LanguageSerializer(read_only=True)
    spoken_languages = LanguageSerializer(many=True, read_only=True)
    badges = UserBadgeSerializer(many=True, read_only=True)
    preferences = UserPreferencesSerializer(read_only=True)
    links = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'bio',
            'is_organizer',
            'native_language',
            'spoken_languages',
            'badges',
            'preferences',
            'is_staff',
            'is_superuser',
            'links'
        ]

    def get_links(self, obj):
        return {
            "self": "/users/me/",
            "update": "/users/me/",
            "badges": "/users/me/badges/",
            "preferences": "/users/me/preferences/"
        }

class UserUpdateSerializer(serializers.ModelSerializer):
    native_language = serializers.PrimaryKeyRelatedField(
        queryset=Language.objects.all(), required=False
    )
    spoken_languages = serializers.PrimaryKeyRelatedField(
        queryset=Language.objects.all(), many=True, required=False
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'bio', 'native_language', 'spoken_languages']

