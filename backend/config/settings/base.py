"""
Django base settings for Conversa project.
This file is shared by all environments (dev, ci, prod).
Each environment file (e.g. dev.py) extends this file.
"""

import os
from pathlib import Path
from datetime import timedelta

# ==============================================================================
# 📁 Chemin de base du projet
# ==============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ==============================================================================
# 📦 Applications installées
# ==============================================================================

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    'rest_framework_simplejwt.token_blacklist',
    "drf_spectacular",
]

PROJECT_APPS = [
    "users",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + PROJECT_APPS

# ==============================================================================
# 🔐 Authentification & API REST
# ==============================================================================

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": [
        "users.permissions.base.IsAuthenticatedAndActive",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.AnonRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "user": "100/min",
        "anon": "10/min",
        "login": "5/min",
        "reset_password": "5/hour",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
}

# ==============================================================================
# 📚 Documentation OpenAPI / Swagger / ReDoc
# ==============================================================================

SPECTACULAR_SETTINGS = {
    "TITLE": "Conversa API",
    "DESCRIPTION": "API RESTful complète pour la plateforme Conversa : utilisateurs, événements, paiements, partenaires...",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "COMPONENT_NO_READ_ONLY_REQUIRED": True,
    "SECURITY": [{"BearerAuth": []}],
    "AUTHENTICATION_WHITELIST": [],
    "COMPONENTS": {
        "securitySchemes": {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            }
        }
    },
    "EXCLUDE_PATH_FORMATS": [
        "/auth/token/",
        "/auth/token/refresh/",
    ],
}

# ==============================================================================
# 🛡️ Middleware et sécurité
# ==============================================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# ==============================================================================
# 📄 Templates
# ==============================================================================

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ==============================================================================
# ⚙️ ASGI / WSGI
# ==============================================================================

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ==============================================================================
# 🌍 Internationalisation
# ==============================================================================

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ==============================================================================
# 📁 Fichiers statiques & médias
# ==============================================================================

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ==============================================================================
# 🔐 Clé secrète et hôtes autorisés (surchargés par env)
# ==============================================================================

SECRET_KEY = os.getenv("SECRET_KEY", "insecure-default-key")
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "localhost").split(",")

# ==============================================================================
# 🔄 Modèle par défaut
# ==============================================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "users.User"

# ==============================================================================
# 📤 Export des variables importantes (pour __init__.py)
# ==============================================================================

__all__ = [
    "BASE_DIR",
    "INSTALLED_APPS",
    "MIDDLEWARE",
    "ROOT_URLCONF",
    "TEMPLATES",
    "WSGI_APPLICATION",
    "ASGI_APPLICATION",
    "LANGUAGE_CODE",
    "TIME_ZONE",
    "USE_I18N",
    "USE_TZ",
    "STATIC_URL",
    "STATIC_ROOT",
    "MEDIA_URL",
    "MEDIA_ROOT",
    "SECRET_KEY",
    "ALLOWED_HOSTS",
    "DEFAULT_AUTO_FIELD",
    "AUTH_USER_MODEL",
    "REST_FRAMEWORK",
    "SPECTACULAR_SETTINGS",
]
