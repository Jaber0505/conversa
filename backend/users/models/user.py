from django.contrib.auth.models import AbstractUser
from django.db import models
from .language import Language

class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)

    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    is_organizer = models.BooleanField(default=False)
    bio = models.TextField(blank=True)

    native_language = models.ForeignKey(
        Language,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="native_speakers"
    )
    spoken_languages = models.ManyToManyField(
        Language,
        blank=True,
        related_name="speakers"
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email
