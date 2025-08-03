from django.db import models

class Language(models.Model):
    code = models.CharField(max_length=10, unique=True)  # ex : "fr", "en"
    name = models.CharField(max_length=50)               # ex : "French", "English"

    def __str__(self):
        return self.name
