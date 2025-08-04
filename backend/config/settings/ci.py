import os
import sys

from .base import *


# ------------------------------
# CI environment (GitHub Actions)
# ------------------------------

DEBUG = False

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "ci-secret-key")

ALLOWED_HOSTS = ["*"]

# ------------------------------
# Database in memory (fast)
# ------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# ------------------------------
# Optimization for testing
# ------------------------------

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "root": {
        "handlers": ["null"],
        "level": "DEBUG",
    },
}

STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
