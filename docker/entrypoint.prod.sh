#!/bin/bash

echo "=== DEBUG: ENVIRONMENT VARIABLES ==="
echo "SECRET_KEY=$SECRET_KEY"
echo "DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE"

echo "📦 Checking migrations plan..."
python manage.py showmigrations

echo "🛠️ Applying migrations..."
python manage.py migrate --noinput

echo "👑 Creating superuser (if needed)..."
python create_superuser.py

echo "🧹 Collecting static files..."
python manage.py collectstatic --noinput

echo "🎯 Starting Gunicorn server..."
gunicorn config.wsgi:application --bind 0.0.0.0:8000
