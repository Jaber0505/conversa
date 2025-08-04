#!/bin/sh

set -e  # Arrête le script si une commande échoue (sauf les "|| echo ...")

echo "📦 Checking migrations plan..."
python manage.py showmigrations --plan || echo "🔍 Migrations check failed"

echo "🛠️ Applying migrations..."
python manage.py migrate --noinput || echo "⚠️ Migrations failed, continuing anyway"

echo "🎯 Starting Gunicorn server..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000
