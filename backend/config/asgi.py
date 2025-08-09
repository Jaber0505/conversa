"""
Point d'entrée ASGI de l'application.
Expose l'application Django pour les serveurs compatibles ASGI (Uvicorn/Daphne),
sans imposer d'environnement : le module de settings est lu via la variable
d’environnement DJANGO_SETTINGS_MODULE (fallback raisonnable en dev).
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.getenv("DJANGO_SETTINGS_MODULE", "config.settings.dev"))

application = get_asgi_application()
