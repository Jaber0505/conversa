# backend/config/settings/base.py
"""
Base settings : API REST sécurisée par défaut (IsAuthenticated), CORS, Swagger (drf-spectacular),
pagination minimale.
"""
from pathlib import Path
import os
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# --- Core ---
SECRET_KEY = os.getenv("SECRET_KEY", "dev-insecure-key")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",") if os.getenv("DJANGO_ALLOWED_HOSTS") else []

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

TEMPLATES = [{
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
}]

# --- DB (définie en dev/prod) ---
DATABASES = {}

# --- Stripe ---
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_CURRENCY = os.getenv("STRIPE_CURRENCY", "eur")

# Flags de test/simulation (gardent le simulateur pour .http)
def _truthy(v: str) -> bool: return str(v).strip().lower() in {"1","true","yes","y","on"}

# Autorise l’endpoint POST /payments/confirm/ (simulateur backend)
STRIPE_CONFIRM_SIMULATOR_ENABLED = _truthy(os.getenv("STRIPE_CONFIRM_SIMULATOR_ENABLED", ""))
# Autorise d’envoyer une carte brute au simulateur (PAN/CVC de test) — à éviter en prod
STRIPE_RAW_CARD_SIM_ENABLED = _truthy(os.getenv("STRIPE_RAW_CARD_SIM_ENABLED", ""))
# Contrôle la stratégie de redirection des AME (Payment Element veut "always")
STRIPE_PI_ALLOW_REDIRECTS = os.getenv("STRIPE_PI_ALLOW_REDIRECTS", "always")  # "always" | "never"

# Optionnel : URL par défaut à passer au confirm backend si Stripe exige un return_url
STRIPE_CONFIRM_RETURN_URL_DEFAULT = os.getenv("STRIPE_CONFIRM_RETURN_URL_DEFAULT", "")

# --- Auth ---
AUTH_USER_MODEL = "users.User"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 9}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Internationalisation ---
LANGUAGE_CODE = "fr"
TIME_ZONE = "Europe/Brussels"
USE_I18N = False
USE_TZ = True

# --- Static/Media ---
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# --- DRF ---
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "users.auth.JWTAuthenticationWithDenylist",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("common.permissions.IsAuthenticatedAndActive",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "common.pagination.DefaultPagination",
    "PAGE_SIZE": 20,
}
REST_FRAMEWORK.update({
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.ScopedRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {
        # Auth
        "auth_register": "5/min",
        "auth_login": "10/min",
        "auth_refresh": "30/min",
        # Events
        "events_read": "120/min",
        "events_write": "20/min",
    },
})
REST_FRAMEWORK["EXCEPTION_HANDLER"] = "config.api_errors.drf_exception_handler"

# --- JWT ---
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

# --- OpenAPI / Swagger ---
SPECTACULAR_SETTINGS = {
    "TITLE": "Conversa API",
    "DESCRIPTION": "API RESTful documentée (Swagger/ReDoc)",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_PATH_PREFIX": r"/api/v1",
    "SECURITY": [{"bearerAuth": []}],
    "SECURITY_SCHEMES": {"bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}},
}

# --- BOOKING ---
BOOKING_TTL_MINUTES = int(os.getenv("DJANGO_BOOKING_TTL_MINUTES", "15"))

# --- LOG ---
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django.request": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "http": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

# --- CORS/CSRF ---
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = os.getenv("DJANGO_CORS_ALLOWED_ORIGINS", "").split(",") if os.getenv("DJANGO_CORS_ALLOWED_ORIGINS") else []
CSRF_TRUSTED_ORIGINS = os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS") else []

# --- Sécurité ---
FORMS_URLFIELD_ASSUME_HTTPS = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = "DENY"
