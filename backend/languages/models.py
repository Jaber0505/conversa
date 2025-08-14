# backend/languages/models.py
from django.db import models

class Language(models.Model):
    code = models.CharField(max_length=8, unique=True)
    label_fr = models.CharField(max_length=100)
    label_en = models.CharField(max_length=100)
    label_nl = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "code"]

    def __str__(self):
        return f"{self.code}"
