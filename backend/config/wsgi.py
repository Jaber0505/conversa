"""
Point d'entrée WSGI de l'application.
Expose l'application Django pour les serveurs compatibles WSGI (ex. Gunicorn),
sans imposer d'environnement : le module de settings est lu via la variable
d’environnement DJANGO_SETTINGS_MODULE (fallback raisonnable en développement).
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.getenv("DJANGO_SETTINGS_MODULE", "config.settings.dev"))

application = get_wsgi_application()
