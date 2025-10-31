"""
Gunicorn configuration for Conversa backend.

Configures logging to filter out health check requests for cleaner logs.
"""
import logging


class SkipHealthzFilter(logging.Filter):
    """Filter to exclude /healthz endpoint from access logs."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Return False if record contains /healthz request."""
        try:
            return "/healthz" not in record.getMessage()
        except Exception:
            return True


# Log to stdout/stderr
accesslog = "-"
errorlog = "-"

# Simple format for access logs (enables filtering)
access_log_format = '%(h)s - "%(r)s" %(s)s'

# Logging configuration
logconfig_dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "skip_healthz": {"()": SkipHealthzFilter},
    },
    "formatters": {
        "generic": {"format": "%(message)s"},
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
    # Target Gunicorn's access and error loggers specifically
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
