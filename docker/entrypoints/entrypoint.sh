#!/usr/bin/env bash
set -euo pipefail

if [ -z "${ENV_MODE:-}" ]; then
  echo "❌ ENV_MODE non défini. Attendu: ci | development | production"
  exit 1
fi

# DJANGO_SETTINGS_MODULE par défaut (surchargable via env)
if [ -z "${DJANGO_SETTINGS_MODULE:-}" ]; then
  case "$ENV_MODE" in
    ci)          export DJANGO_SETTINGS_MODULE="config.settings.ci"  ;;
    production)  export DJANGO_SETTINGS_MODULE="config.settings.prod" ;;
    development) export DJANGO_SETTINGS_MODULE="config.settings.dev"  ;;
    *)           export DJANGO_SETTINGS_MODULE="config.settings.dev"  ;;
  esac
fi

export PYTHONPATH="${PYTHONPATH:-/app/backend}"
echo "🔧 ENTRYPOINT | ENV_MODE=$ENV_MODE | DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE"

case "$ENV_MODE" in
  ci)          exec /entrypoints/entrypoint.ci.sh ;;
  development) exec /entrypoints/entrypoint.dev.sh ;;
  production)  exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers "${GUNICORN_WORKERS:-4}" --threads "${GUNICORN_THREADS:-4}" --timeout "${GUNICORN_TIMEOUT:-120}" ;;
esac
