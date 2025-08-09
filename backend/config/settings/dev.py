"""
Paramètres Django - Développement local (Docker Compose).
"""

from __future__ import annotations

import os
from dotenv import load_dotenv

from .base import *  # noqa: F403

# ── Env .env.dev (non versionné)
env_path = BASE_DIR / "docker" / "env" / ".env.dev"  # noqa: F405
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

# ── Général
DEBUG = os.getenv("DEBUG", "true").lower() in {"true", "1", "yes"}
SECRET_KEY = os.getenv("SECRET_KEY", "dev-insecure-key")
ALLOWED_HOSTS = [h.strip() for h in os.getenv("DJANGO_ALLOWED_HOSTS", "*").split(",") if h.strip()]

# ── CORS permissif en dev
CSRF_TRUSTED_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
CORS_ALLOW_ALL_ORIGINS = True

# ── Base de données (service "db" du compose)
DATABASES = {
    "default": {
        "ENGINE": os.getenv("DJANGO_DB_ENGINE", "django.db.backends.postgresql"),
        "NAME": os.getenv("DJANGO_DB_NAME", "conversa_db"),
        "USER": os.getenv("DJANGO_DB_USER", "postgres"),
        "PASSWORD": os.getenv("DJANGO_DB_PASSWORD", "postgres"),
        "HOST": os.getenv("DJANGO_DB_HOST", "db"),
        "PORT": os.getenv("DJANGO_DB_PORT", "5432"),
    }
}

# ── Debug toolbar (optionnel)
if os.getenv("USE_DEBUG_TOOLBAR", "false").lower() in {"true", "1", "yes"}:
    INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa: F405
    INTERNAL_IPS = ["127.0.0.1"]
