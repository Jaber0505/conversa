"""
Paramètres Django - Production (Render).
Variables sensibles injectées via l'hébergeur / secrets.
"""

from __future__ import annotations

import os

from .base import *  # noqa: F403

# ── Sécurité de base
DEBUG = os.getenv("DEBUG", "0") in {"1", "true", "True"}
if DEBUG:
    raise Exception("[SECURITY] DEBUG doit être désactivé en production.")

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise Exception("[CRITICAL] SECRET_KEY manquante.")

ALLOWED_HOSTS_ENV = os.getenv("DJANGO_ALLOWED_HOSTS", "")
if not ALLOWED_HOSTS_ENV:
    raise Exception("[CRITICAL] DJANGO_ALLOWED_HOSTS manquant.")
ALLOWED_HOSTS = [h.strip() for h in ALLOWED_HOSTS_ENV.split(",") if h.strip()]

# ── CORS / CSRF
CORS_ALLOWED_ORIGINS = [
    o.strip() for o in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if o.strip()
]
CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()
]

# ── Base de données (Render Postgres + SSL)
DATABASES = {
    "default": {
        "ENGINE": os.getenv("DJANGO_DB_ENGINE", "django.db.backends.postgresql"),
        "NAME": os.getenv("DJANGO_DB_NAME"),
        "USER": os.getenv("DJANGO_DB_USER"),
        "PASSWORD": os.getenv("DJANGO_DB_PASSWORD"),
        "HOST": os.getenv("DJANGO_DB_HOST"),
        "PORT": os.getenv("DJANGO_DB_PORT", "5432"),
        "OPTIONS": {"sslmode": os.getenv("DJANGO_DB_SSLMODE", "require")},
        "CONN_MAX_AGE": 600,
    }
}

# ── Statics Django (si servis par l'app; sinon laisse Nginx du frontend)
# Active WhiteNoise uniquement si tu sers les statics Django ici.
if os.getenv("ENABLE_WHITENOISE", "0") in {"1", "true", "True"}:
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")  # noqa: F405
    STORAGES = {
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    }

# ── Sécurité HTTP renforcée
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ── Logging
LOG_LEVEL = os.getenv("DJANGO_LOG_LEVEL", "INFO").upper()
if LOG_LEVEL not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
    LOG_LEVEL = "INFO"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"verbose": {"format": "{levelname} {asctime} {module} {message}", "style": "{"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "verbose"}},
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
}

# ── Variables critiques obligatoires
REQUIRED_VARS = [
    "SECRET_KEY",
    "DJANGO_ALLOWED_HOSTS",
    "DJANGO_DB_NAME",
    "DJANGO_DB_USER",
    "DJANGO_DB_PASSWORD",
    "DJANGO_DB_HOST",
    "DJANGO_DB_PORT",
]
_missing = [v for v in REQUIRED_VARS if not os.getenv(v)]
if _missing:
    raise Exception(f"[CRITICAL] Variables manquantes : {', '.join(_missing)}")
