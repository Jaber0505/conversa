"""
Configuration de développement.
PostgreSQL local (Docker), DEBUG activé, CORS/CSRF ouverts pour Angular (localhost:4200),
journalisation verbeuse.
"""
from .base import *  # noqa
import os

def _truthy(v: str) -> bool: return str(v).strip().lower() in {"1","true","yes","y","on"}
# On lit/écrase les flags ici si nécessaire (sinon hérités de base.py)
STRIPE_CONFIRM_SIMULATOR_ENABLED = _truthy(os.getenv("STRIPE_CONFIRM_SIMULATOR_ENABLED", os.getenv("SIMULATOR", "1")))
STRIPE_RAW_CARD_SIM_ENABLED = _truthy(os.getenv("STRIPE_RAW_CARD_SIM_ENABLED", "1"))
STRIPE_PI_ALLOW_REDIRECTS = os.getenv("STRIPE_PI_ALLOW_REDIRECTS", "always")

DEBUG = True
SECRET_KEY = os.getenv("SECRET_KEY", "dev-insecure-key")
ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DJANGO_DB_NAME", "conversa_db"),
        "USER": os.getenv("DJANGO_DB_USER", "postgres"),
        "PASSWORD": os.getenv("DJANGO_DB_PASSWORD", "postgres"),
        "HOST": os.getenv("DJANGO_DB_HOST", "db"),
        "PORT": os.getenv("DJANGO_DB_PORT", "5432"),
        "ATOMIC_REQUESTS": True,
    }
}

CORS_ALLOWED_ORIGINS = [
    "http://localhost:4200",
    "http://127.0.0.1:4200",
]
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:4200",
    "http://127.0.0.1:4200",
]

LOGGING["root"]["level"] = "DEBUG"  # noqa: F405
