from django.db import models
from .user import User

class UserBadge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="badges")
    label = models.CharField(max_length=255)
    earned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.label}"
