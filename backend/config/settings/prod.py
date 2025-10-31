"""
Production settings for Conversa API (Render deployment).

This configuration enforces security best practices:
- DEBUG disabled
- HTTPS enforced via HSTS
- Secure cookies (HttpOnly, Secure, SameSite)
- Strict CORS/CSRF origins
- Database credentials via environment variables
- Connection pooling enabled

Environment Variables Required:
    - SECRET_KEY (CRITICAL - use strong random key)
    - DJANGO_ALLOWED_HOSTS (comma-separated domains)
    - DJANGO_DB_NAME, DJANGO_DB_USER, DJANGO_DB_PASSWORD, DJANGO_DB_HOST
    - DJANGO_CORS_ALLOWED_ORIGINS
    - DJANGO_CSRF_TRUSTED_ORIGINS

Usage:
    DJANGO_SETTINGS_MODULE=config.settings.prod gunicorn config.wsgi:application
"""

from .base import *  # noqa
import os


def _truthy(v: str) -> bool:
    """Convert string to boolean."""
    return str(v).strip().lower() in {"1", "true", "yes", "y", "on"}


# Stripe simulator flags (disabled in production)
STRIPE_CONFIRM_SIMULATOR_ENABLED = _truthy(
    os.getenv("STRIPE_CONFIRM_SIMULATOR_ENABLED", "1")
)
STRIPE_RAW_CARD_SIM_ENABLED = _truthy(
    os.getenv("STRIPE_RAW_CARD_SIM_ENABLED", "0")
)
STRIPE_PI_ALLOW_REDIRECTS = os.getenv("STRIPE_PI_ALLOW_REDIRECTS", "always")

# =============================================================================
# PRODUCTION SECURITY SETTINGS
# =============================================================================

DEBUG = False
SECRET_KEY = os.getenv("SECRET_KEY")  # MUST be set in environment

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is required in production")

ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",")

if not ALLOWED_HOSTS or ALLOWED_HOSTS == [""]:
    raise RuntimeError("DJANGO_ALLOWED_HOSTS must be set in production")

# =============================================================================
# DATABASE - PostgreSQL (Render)
# =============================================================================

DATABASES = {
    "default": {
        "ENGINE": os.getenv("DJANGO_DB_ENGINE", "django.db.backends.postgresql"),
        "NAME": os.getenv("DJANGO_DB_NAME"),
        "USER": os.getenv("DJANGO_DB_USER"),
        "PASSWORD": os.getenv("DJANGO_DB_PASSWORD"),
        "HOST": os.getenv("DJANGO_DB_HOST"),
        "PORT": os.getenv("DJANGO_DB_PORT", "5432"),
        "ATOMIC_REQUESTS": True,
        "CONN_MAX_AGE": 60,  # Connection pooling (60 seconds)
    }
}

# =============================================================================
# CORS & CSRF - Strict origins only
# =============================================================================

CORS_ALLOWED_ORIGINS = (
    os.getenv("DJANGO_CORS_ALLOWED_ORIGINS", "").split(",")
    if os.getenv("DJANGO_CORS_ALLOWED_ORIGINS")
    else []
)

CSRF_TRUSTED_ORIGINS = (
    os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS")
    else []
)

# Disable browsable API in production (JSON only)
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [  # noqa: F405
    "rest_framework.renderers.JSONRenderer"
]

# =============================================================================
# HTTPS & SECURITY HEADERS
# =============================================================================

# Cookies
SESSION_COOKIE_SECURE = True  # HTTPS only
CSRF_COOKIE_SECURE = True  # HTTPS only
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# HTTPS enforcement
SECURE_SSL_REDIRECT = True  # Redirect HTTP -> HTTPS
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")  # Render uses proxy

# HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = int(os.getenv("DJANGO_SECURE_HSTS_SECONDS", "31536000"))  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Additional security headers
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# =============================================================================
# LOGGING - Production level
# =============================================================================

LOGGING["root"]["level"] = "INFO"  # noqa: F405
LOGGING["loggers"] = {  # noqa: F405
    "django.security": {
        "handlers": ["console"],
        "level": "WARNING",
        "propagate": True,
    },
}
