from .base import *
import os

# ------------------------------
# CI ENVIRONMENT
# ------------------------------

DEBUG = False
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "ci-secret-key")

ALLOWED_HOSTS = ["*"]  # en CI on teste souvent sans host restriction

# ------------------------------
# In-memory test database
# ------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# ------------------------------
# Optimisations pour tests
# ------------------------------

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
