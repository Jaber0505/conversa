"""
Language model for multilingual support.

This module defines the Language model which represents available languages
for the platform (used in User profiles and Events).
"""
from django.db import models


class Language(models.Model):
    """
    Language reference model.

    Represents a language available on the platform with translations
    in French, English, and Dutch (Belgium's official languages).

    Used by:
    - Users: native_langs and target_langs (ManyToMany)
    - Events: language field (ForeignKey) for event language

    Examples:
        >>> lang_fr = Language.objects.get(code="fr")
        >>> print(lang_fr.label_en)
        "French"
    """

    code = models.CharField(
        max_length=8,
        unique=True,
        db_index=True,
        help_text="ISO 639-1 language code (e.g., 'fr', 'en', 'nl')"
    )
    label_fr = models.CharField(
        max_length=100,
        help_text="Language name in French (e.g., 'Français')"
    )
    label_en = models.CharField(
        max_length=100,
        help_text="Language name in English (e.g., 'French')"
    )
    label_nl = models.CharField(
        max_length=100,
        help_text="Language name in Dutch (e.g., 'Frans')"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this language is available for selection"
    )
    sort_order = models.PositiveSmallIntegerField(
        default=100,
        help_text="Display order (lower numbers appear first)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when language was added"
    )

    class Meta:
        ordering = ["sort_order", "code"]
        verbose_name = "Language"
        verbose_name_plural = "Languages"

    def __str__(self):
        """Return language code as string representation."""
        return self.code

    def get_label(self, locale="en"):
        """
        Get language label in specified locale.

        Args:
            locale: Language code for label ('fr', 'en', 'nl')

        Returns:
            str: Language label in requested locale, defaults to English

        Example:
            >>> lang = Language.objects.get(code="fr")
            >>> lang.get_label("en")
            "French"
            >>> lang.get_label("nl")
            "Frans"
        """
        return getattr(self, f"label_{locale}", self.label_en)
