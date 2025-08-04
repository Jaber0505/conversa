#!/bin/sh

echo "=== DEBUG: ENVIRONMENT VARIABLES ==="
printenv | grep SECRET_KEY
printenv | grep DJANGO_SETTINGS_MODULE

echo "📦 Checking migrations plan..."
python manage.py showmigrations --plan || echo "🔍 Migrations check failed"

echo "🛠️ Applying migrations..."
python manage.py migrate || echo "⚠️ Migrations failed, continuing anyway"

echo "🎯 Starting Gunicorn server..."
gunicorn config.wsgi:application --bind 0.0.0.0:8000
