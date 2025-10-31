"""Partners application configuration."""
from django.apps import AppConfig


class PartnersConfig(AppConfig):
    """
    Configuration for the partners application.

    This app manages partner venues (cafes, bars) that host language exchange events.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "partners"
    verbose_name = "Partner Venues"
