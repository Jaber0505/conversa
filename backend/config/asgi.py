"""
ASGI config for Conversa API.

ASGI (Asynchronous Server Gateway Interface) is used for async servers
like Uvicorn, Daphne, or Hypercorn.

For WebSockets or async views, use this instead of wsgi.py.

Usage:
    uvicorn config.asgi:application --reload
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

application = get_asgi_application()
