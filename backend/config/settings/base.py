"""
Base Django settings for Conversa API.

This module contains shared configuration used by both development and production environments.

Features:
- Secure REST API (IsAuthenticated by default)
- CORS configuration
- JWT authentication with token blacklisting
- Swagger/ReDoc documentation (drf-spectacular)
- Rate limiting (throttling)
- Custom exception handling
"""

from pathlib import Path
import os
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# =============================================================================
# CORE DJANGO SETTINGS
# =============================================================================

SECRET_KEY = os.getenv("SECRET_KEY", "dev-insecure-key")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
ALLOWED_HOSTS = (
    os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",")
    if os.getenv("DJANGO_ALLOWED_HOSTS")
    else []
)

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_filters",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "corsheaders",
]

PROJECT_APPS = [
    "audit",
    "languages",
    "users",
    "events",
    "bookings",
    "payments",
    "partners",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + PROJECT_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "common.middleware.request_log.RequestLogMiddleware",
    "audit.middleware.AuditMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

# =============================================================================
# DATABASE
# =============================================================================
# Database configuration is defined in dev.py and prod.py
DATABASES = {}

# =============================================================================
# STRIPE PAYMENT CONFIGURATION
# =============================================================================

STRIPE_SECRET_KEY = os.getenv("DJANGO_STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("DJANGO_STRIPE_WEBHOOK_SECRET", "")
STRIPE_CURRENCY = (os.getenv("DJANGO_STRIPE_CURRENCY", "eur") or "eur").lower()

FRONTEND_BASE_URL = os.getenv(
    "DJANGO_FRONTEND_BASE_URL", "http://localhost:4200"
).rstrip("/")


def _with_leading_slash(p: str, default: str) -> str:
    """Ensure path starts with leading slash."""
    p = (p or default).strip()
    return p if p.startswith("/") else "/" + p


STRIPE_SUCCESS_PATH = _with_leading_slash(
    os.getenv("DJANGO_STRIPE_SUCCESS_PATH", "/stripe/success"), "/stripe/success"
)
STRIPE_CANCEL_PATH = _with_leading_slash(
    os.getenv("DJANGO_STRIPE_CANCEL_PATH", "/stripe/cancel"), "/stripe/cancel"
)

# Security check: Only allow Stripe TEST keys
if STRIPE_SECRET_KEY and not STRIPE_SECRET_KEY.startswith("sk_test_"):
    raise RuntimeError(
        "Stripe TEST mode only: STRIPE_SECRET_KEY must start with 'sk_test_'."
    )

# =============================================================================
# AUTHENTICATION & USER MODEL
# =============================================================================

AUTH_USER_MODEL = "users.User"
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 9},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# =============================================================================
# INTERNATIONALIZATION
# =============================================================================

LANGUAGE_CODE = "fr"
TIME_ZONE = "Europe/Brussels"
USE_I18N = False
USE_TZ = True

# =============================================================================
# STATIC & MEDIA FILES
# =============================================================================

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Fixtures
FIXTURE_DIRS = [BASE_DIR / "fixtures"]

# =============================================================================
# DJANGO REST FRAMEWORK
# =============================================================================

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "users.auth.JWTAuthenticationWithDenylist",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("common.permissions.IsAuthenticatedAndActive",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "common.pagination.DefaultPagination",
    "PAGE_SIZE": 20,
}

# Rate limiting (throttling)
REST_FRAMEWORK.update({
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        # Global limits
        "anon": "100/hour",  # Anonymous users: 100 requests/hour
        "user": "1000/hour",  # Authenticated users: 1000 requests/hour
        # Authentication endpoints (more restrictive)
        "auth_register": "5/hour",  # Prevent registration spam
        "auth_login": "10/min",  # Prevent brute force
        "auth_refresh": "30/min",  # Normal usage
        # Events endpoints
        "events_read": "120/min",
        "events_write": "20/min",
        # Bookings endpoints
        "bookings_create": "30/hour",  # Prevent booking spam
        "bookings_cancel": "10/hour",  # Prevent abuse
        # Payments endpoints
        "payments_create": "20/hour",  # Prevent payment spam
    },
})

# Custom exception handler for consistent error responses
REST_FRAMEWORK["EXCEPTION_HANDLER"] = "config.api_errors.drf_exception_handler"

# =============================================================================
# JWT AUTHENTICATION (SimpleJWT)
# =============================================================================

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# =============================================================================
# API DOCUMENTATION (Swagger/ReDoc)
# =============================================================================

SPECTACULAR_SETTINGS = {
    "TITLE": "Conversa API",
    "DESCRIPTION": "RESTful API for language exchange event platform",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_PATH_PREFIX": r"/api/v1",
    # Security: Bearer JWT authentication
    "SECURITY": [{"bearerAuth": []}],
    "SECURITY_SCHEMES": {
        "bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
    },
    # Tag descriptions for better API organization
    "TAGS": [
        {
            "name": "Auth",
            "description": "User authentication, registration, and profile management. Includes JWT token operations (login, refresh, logout)."
        },
        {
            "name": "Events",
            "description": "Language exchange events management. Users can browse, create, and manage events hosted at partner venues."
        },
        {
            "name": "Bookings",
            "description": "Event bookings and cancellations. Users can reserve spots for events and manage their reservations."
        },
        {
            "name": "Payments",
            "description": "Payment processing via Stripe. Includes checkout session creation and webhook handling for payment confirmations."
        },
        {
            "name": "Partners",
            "description": "Partner venues that host language exchange events. Admin-only management of venue information and capacity."
        },
        {
            "name": "Languages",
            "description": "Available languages for language exchange. Read-only list of supported native and target languages."
        },
        {
            "name": "Audit",
            "description": "Audit logging system for admin monitoring. Tracks system events, errors, and user actions for security and debugging."
        },
    ],
    # Swagger UI configuration
    "SWAGGER_UI_SETTINGS": {
        "persistAuthorization": True,  # Persist auth token across page reloads
        "displayRequestDuration": True,  # Show request duration
        "docExpansion": "none",  # Collapse all sections by default
        "filter": True,  # Enable search/filter
    },
}

# Additional security schemes configuration
SPECTACULAR_SETTINGS.update({
    "APPEND_COMPONENTS": {
        "securitySchemes": {
            "bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
        }
    }
})

# =============================================================================
# BUSINESS LOGIC CONFIGURATION
# =============================================================================

# Booking expiration time in minutes
BOOKING_TTL_MINUTES = int(os.getenv("DJANGO_BOOKING_TTL_MINUTES", "15"))

# TEMPORARY: Initial staff creation secret (DELETE AFTER CREATING STAFF USER!)
# Set via: DJANGO_INITIAL_STAFF_SECRET environment variable
INITIAL_STAFF_SECRET = os.getenv("DJANGO_INITIAL_STAFF_SECRET", "")

# =============================================================================
# SCHEDULED TASKS CONFIGURATION
# =============================================================================

# Auto-cancellation check interval (used by Render Cron Jobs)
AUTO_CANCEL_CHECK_INTERVAL_MINUTES = int(
    os.getenv("DJANGO_AUTO_CANCEL_CHECK_INTERVAL", "15")
)

# =============================================================================
# LOGGING
# =============================================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d) - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "http": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "payments.webhook": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        # Application loggers
        "event": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "booking": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "payment": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "stripe": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "conversa": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# =============================================================================
# CORS & CSRF CONFIGURATION
# =============================================================================

CORS_ALLOW_CREDENTIALS = True
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

# =============================================================================
# SECURITY SETTINGS
# =============================================================================

FORMS_URLFIELD_ASSUME_HTTPS = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = "DENY"
