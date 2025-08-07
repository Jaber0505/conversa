"""
Django settings - ENV: Production (Render)
This file is used in a live environment.
All variables are injected by Render (or GitHub Actions upstream).
"""

import os
from .base import *

# ==============================================================================
# Debug (must be disabled in production)
# ==============================================================================

DEBUG = os.getenv("DEBUG", "False").lower() == "true"

if DEBUG:
    raise Exception("[SECURITY] DEBUG must be False in production.")

# ==============================================================================
# Secret key (mandatory for production, no fallback)
# ==============================================================================

SECRET_KEY = os.environ["SECRET_KEY"]

# ==============================================================================
# Authorized hosts (mandatory for prod)
# ==============================================================================

ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",")
if not any(ALLOWED_HOSTS):
    raise Exception("[SECURITY] ALLOWED_HOSTS must not be empty in production.")

# ==============================================================================
# PostgreSQL database
# ==============================================================================

DATABASES = {
    "default": {
        "ENGINE": os.environ["DJANGO_DB_ENGINE"],
        "NAME": os.environ["DJANGO_DB_NAME"],
        "USER": os.environ["DJANGO_DB_USER"],
        "PASSWORD": os.environ["DJANGO_DB_PASSWORD"],
        "HOST": os.environ["DJANGO_DB_HOST"],
        "PORT": os.environ["DJANGO_DB_PORT"],
    }
}

# ==============================================================================
# Gestion des fichiers statiques via WhiteNoise
# ==============================================================================

MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

WHITENOISE_AUTOREFRESH = False
WHITENOISE_USE_FINDERS = False

# ==============================================================================
# Sécurité (headers, cookies, SSL, etc.)
# ==============================================================================

SECURE_HSTS_SECONDS = 31536000  # 1 an
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
X_FRAME_OPTIONS = "DENY"

# ==============================================================================
# Logging (stdout, format structuré)
# ==============================================================================

LOG_LEVEL = os.getenv("DJANGO_LOG_LEVEL", "INFO").upper()
if LOG_LEVEL not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
    LOG_LEVEL = "INFO"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
}

DEFAULT_RESPONSE_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-Conversa-Version": "1.0.0",
}

# ============================================================================== #
# Sanity check – fail early if critical env vars are missing                    #
# ============================================================================== #

REQUIRED_VARS = [
    "SECRET_KEY",
    "DJANGO_ALLOWED_HOSTS",
    "DJANGO_DB_NAME",
    "DJANGO_DB_USER",
    "DJANGO_DB_PASSWORD",
    "DJANGO_DB_HOST",
    "DJANGO_DB_PORT",
]

for var in REQUIRED_VARS:
    if not os.getenv(var):
        raise Exception(f"[CRITICAL] Missing environment variable: {var}")