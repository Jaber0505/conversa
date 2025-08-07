"""
Django settings – ENV: Continuous Integration (CI)
Utilisé exclusivement dans les pipelines automatisées (GitHub Actions, etc.)
Optimisé pour la vitesse d’exécution des tests unitaires avec SQLite en mémoire.
"""

from .base import *
import os

# ==============================================================================
# Environnement CI (GitHub Actions, etc.)
# ==============================================================================

DEBUG = os.getenv("CI_DEBUG", "False").lower() in ("true", "1", "yes")
SECRET_KEY = os.getenv("CI_SECRET_KEY", "ci-secret-key")
ALLOWED_HOSTS = os.getenv("CI_DJANGO_ALLOWED_HOSTS", "*").split(",")

# ==============================================================================
# Base de données SQLite (ultra rapide, en mémoire)
# ==============================================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# ==============================================================================
# Performances & simplifications pour les tests
# ==============================================================================

REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {}

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {
        "null": {"class": "logging.NullHandler"},
    },
    "root": {
        "handlers": ["null"],
        "level": "DEBUG",
    },
}

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ==============================================================================
# Autres paramètres nécessaires
# ==============================================================================

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
