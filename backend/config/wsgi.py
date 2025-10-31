"""
WSGI config for Conversa API.

WSGI (Web Server Gateway Interface) is used for production deployment
with Gunicorn or uWSGI.

This is the standard production configuration used by Render.

Usage:
    gunicorn config.wsgi:application --workers 4 --bind 0.0.0.0:8000
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")

application = get_wsgi_application()
