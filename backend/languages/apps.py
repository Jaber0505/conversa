"""Languages application configuration."""
from django.apps import AppConfig


class LanguagesConfig(AppConfig):
    """
    Configuration for the languages application.

    This app manages the available languages on the platform,
    used for user profiles and event language selection.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "languages"
    verbose_name = "Languages"
