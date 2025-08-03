from django.db import models
from .user import User

class UserPreferences(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="preferences")
    receive_notifications = models.BooleanField(default=True)
    ui_language = models.CharField(max_length=10, default="en")  # langue de l'interface

    def __str__(self):
        return f"Prefs for {self.user.email}"
