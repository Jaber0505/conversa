#!/bin/bash

echo "=== DEBUG: ENVIRONMENT VARIABLES ==="
echo "SECRET_KEY=$SECRET_KEY"
echo "DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE"

set -e

echo "📦 Running migrations..."
python manage.py migrate --noinput

echo "👑 Creating superuser (if needed)..."
python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email="admin@conversa.be").exists():
    User.objects.create_superuser("admin@conversa.be", "admin123")
    print("✅ Superuser created.")
else:
    print("ℹ️ Superuser already exists.")
END

echo "🧹 Collecting static files..."
python manage.py collectstatic --noinput

echo "🚀 Starting Gunicorn..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000
