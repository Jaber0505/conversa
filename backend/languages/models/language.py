#languages/models/language.py
from django.core.validators import RegexValidator
from django.db import models

iso_code_validator = RegexValidator(
    regex=r'^[a-z]{2}$',  # ISO 639-1 (ex: fr, en, nl)
    message="Use a 2-letter ISO 639-1 lowercase code (e.g. 'fr', 'en')."
)

class Language(models.Model):
    code = models.CharField(
        max_length=10,
        unique=True,
        db_index=True,
        validators=[iso_code_validator],
        help_text="ISO 639-1 code (e.g., fr, en, nl)."
    )
    names = models.JSONField(
        default=dict,
        help_text="Labels by locale, e.g. {'fr':'Français','en':'French','nl':'Frans'}."
    )
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=100)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "code"]
        verbose_name = "Langue"
        verbose_name_plural = "Langues"

    def __str__(self) -> str:
        return self.code
