# backend/config/settings/dev.py
"""
Configuration de développement.
PostgreSQL local (Docker), DEBUG activé, CORS/CSRF ouverts pour Angular (localhost:4200),
journalisation verbeuse.
"""

from .base import *  # noqa
import os

DEBUG = True
SECRET_KEY = os.getenv("SECRET_KEY", "dev-insecure-key")
ALLOWED_HOSTS = ["*"] #["localhost", "127.0.0.1"]

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
