from rest_framework import serializers
from users.models import UserBadge

class UserBadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserBadge
        fields = ['label', 'earned_at']
