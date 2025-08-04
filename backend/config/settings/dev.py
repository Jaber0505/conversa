import os

from .base import *
from dotenv import load_dotenv

# ------------------------------
# Environment DEV
# ------------------------------

load_dotenv()

DEBUG = os.getenv("DJANGO_DEBUG", "True") == "True"

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret-key")

ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# ------------------------------
# Local database
# ------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DJANGO_DB_NAME", "conversadb"),
        "USER": os.getenv("DJANGO_DB_USER", "postgres"),
        "PASSWORD": os.getenv("DJANGO_DB_PASSWORD", "postgres"),
        "HOST": os.getenv("DJANGO_DB_HOST", "localhost"),
        "PORT": os.getenv("DJANGO_DB_PORT", "5432"),
    }
}

# ------------------------------
# Debug toolbar (optionnel)
# ------------------------------

if os.getenv("USE_DEBUG_TOOLBAR", "False") == "True":
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")

    INTERNAL_IPS = [
        "127.0.0.1",
    ]
