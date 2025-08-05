"""
Django settings - ENV: Development
Used for local development.
Variables are loaded from `.env.dev` via python-dotenv.
"""

import os
from dotenv import load_dotenv
from .base import *

# ============================================================================== #
# Load local .env.dev file (unversioned, for dev only)
# ============================================================================== #

load_dotenv()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

# ============================================================================== #
# Debug & security keys
# ============================================================================== #

DEBUG = os.getenv("DEBUG", "True") == "True"
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# ============================================================================== #
# Local PostgreSQL database
# ============================================================================== #

DATABASES = {
    "default": {
        "ENGINE": os.getenv("DJANGO_DB_ENGINE", "django.db.backends.postgresql"),
        "NAME": os.getenv("DJANGO_DB_NAME", "conversadb"),
        "USER": os.getenv("DJANGO_DB_USER", "postgres"),
        "PASSWORD": os.getenv("DJANGO_DB_PASSWORD", "postgres"),
        "HOST": os.getenv("DJANGO_DB_HOST", "localhost"),
        "PORT": os.getenv("DJANGO_DB_PORT", "5432"),
    }
}

# ============================================================================== #
# Optional: dev-only extensions (e.g. debug toolbar)
# ============================================================================== #

if os.getenv("USE_DEBUG_TOOLBAR", "False") == "True":
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
    INTERNAL_IPS = ["127.0.0.1"]
