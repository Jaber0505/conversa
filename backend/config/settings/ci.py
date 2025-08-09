"""
Paramètres Django - Intégration continue (CI).
Tests rapides avec SQLite en mémoire.
"""

from __future__ import annotations

import os

from .base import *  # noqa: F403

# ── Général
DEBUG = os.getenv("CI_DEBUG", "false").lower() in {"true", "1", "yes"}
SECRET_KEY = os.getenv("CI_SECRET_KEY", "ci-insecure-key")
ALLOWED_HOSTS = [h.strip() for h in os.getenv("CI_DJANGO_ALLOWED_HOSTS", "*").split(",") if h.strip()]

# ── DB SQLite (mémoire)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# ── CORS permissif pour la CI
CORS_ALLOW_ALL_ORIGINS = True

# ── Tests plus rapides
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []  # type: ignore[name-defined]  # noqa: F405
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {  # type: ignore[name-defined]  # noqa: F405
    "user": "100/min",
    "anon": "10/min",
    "login": "5/min",
    "reset_password": "5/hour",
}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# ── Logging minimal
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {"null": {"class": "logging.NullHandler"}},
    "root": {"handlers": ["null"], "level": "WARNING"},
}

# ── URLs / WSGI / ASGI (clarifiés)
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"  # noqa: F405
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"  # noqa: F405
