import os
from importlib import import_module

ENV_MODE = os.getenv("ENV_MODE", "development").lower()

settings_module = {
    "development": "config.settings.dev",
    "ci": "config.settings.ci",
    "production": "config.settings.prod",
}.get(ENV_MODE)

if not settings_module:
    raise RuntimeError(f"Variable ENV_MODE invalide ou non supportée : {ENV_MODE}")

# Charge dynamiquement le module settings demandé
settings = import_module(settings_module)

# Expose toutes les variables du module settings chargé au namespace global
globals().update({k: getattr(settings, k) for k in dir(settings) if not k.startswith("_")})
