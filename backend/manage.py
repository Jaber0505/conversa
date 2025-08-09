#!/usr/bin/env python
"""
Point d’entrée en ligne de commande pour Django.
- Utilise la variable d’environnement DJANGO_SETTINGS_MODULE si définie.
- Par défaut, bascule sur 'config.settings.dev' pour le développement.
- Permet d’exécuter les commandes Django (migrate, runserver, createsuperuser, etc.).
"""

import os
import sys


def main() -> None:
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        os.getenv("DJANGO_SETTINGS_MODULE", "config.settings.dev"),
    )
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Impossible d’importer Django. Vérifie que les dépendances sont installées "
            "(pip install -r requirements/dev.txt) et que l’environnement Python est actif."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
