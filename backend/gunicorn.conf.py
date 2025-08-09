import logging

# Évite de logguer les requêtes d'accès sur /healthz
class SkipHealthzFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # record.getMessage() contient la ligne d'accès: 'IP - "GET /healthz HTTP/1.1" 200 ...'
        try:
            return "/healthz" not in record.getMessage()
        except Exception:
            return True

# Fichiers de log: stdout
accesslog = "-"
errorlog = "-"
# Format simple (contient la requête → exploitable par le filtre)
access_log_format = '%(h)s - "%(r)s" %(s)s'

logconfig_dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "skip_healthz": { "()": SkipHealthzFilter },
    },
    "formatters": {
        "generic": { "format": "%(message)s" },
    },
    "handlers": {
        "console_access": {
            "class": "logging.StreamHandler",
            "filters": ["skip_healthz"],
            "formatter": "generic",
        },
        "console_error": {
            "class": "logging.StreamHandler",
            "formatter": "generic",
        },
    },
    # On cible spécifiquement le logger d'accès de gunicorn
    "loggers": {
        "gunicorn.access": {
            "handlers": ["console_access"],
            "level": "INFO",
            "propagate": False,
        },
        "gunicorn.error": {
            "handlers": ["console_error"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console_error"],
        "level": "INFO",
    },
}
