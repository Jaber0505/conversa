"""
Development settings for Conversa API.

This configuration is optimized for local development with:
- DEBUG mode enabled for detailed error pages
- CORS open to localhost:4200 (Angular frontend)
- PostgreSQL running in Docker
- Verbose logging for debugging
- Insecure defaults for SECRET_KEY (NEVER use in production)

Usage:
    DJANGO_SETTINGS_MODULE=config.settings.dev python manage.py runserver
"""

from .base import *  # noqa
import os


def _truthy(v: str) -> bool:
    """Convert string to boolean."""
    return str(v).strip().lower() in {"1", "true", "yes", "y", "on"}


# Stripe simulator flags (for local testing without real Stripe calls)
STRIPE_CONFIRM_SIMULATOR_ENABLED = _truthy(
    os.getenv("STRIPE_CONFIRM_SIMULATOR_ENABLED", os.getenv("SIMULATOR", "1"))
)
STRIPE_RAW_CARD_SIM_ENABLED = _truthy(
    os.getenv("STRIPE_RAW_CARD_SIM_ENABLED", "1")
)
STRIPE_PI_ALLOW_REDIRECTS = os.getenv("STRIPE_PI_ALLOW_REDIRECTS", "always")

# =============================================================================
# DEVELOPMENT OVERRIDES
# =============================================================================

DEBUG = True
SECRET_KEY = os.getenv("SECRET_KEY", "dev-insecure-key-change-in-production")
ALLOWED_HOSTS = ["*"]  # Allow all hosts in development

# =============================================================================
# DATABASE - Local PostgreSQL (Docker)
# =============================================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DJANGO_DB_NAME", "conversa_db"),
        "USER": os.getenv("DJANGO_DB_USER", "postgres"),
        "PASSWORD": os.getenv("DJANGO_DB_PASSWORD", "postgres"),
        "HOST": os.getenv("DJANGO_DB_HOST", "db"),  # Docker service name
        "PORT": os.getenv("DJANGO_DB_PORT", "5432"),
        "ATOMIC_REQUESTS": True,
    }
}

# =============================================================================
# CORS - Open to local Angular frontend
# =============================================================================

CORS_ALLOWED_ORIGINS = [
    "http://localhost:4200",
    "http://127.0.0.1:4200",
]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:4200",
    "http://127.0.0.1:4200",
]

# =============================================================================
# LOGGING - Verbose for debugging
# =============================================================================

LOGGING["root"]["level"] = "DEBUG"  # noqa: F405
