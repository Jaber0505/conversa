#!/bin/bash
set -e

echo "🌍 ENV_MODE=$ENV_MODE"
echo "📦 DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE"

if [ -z "$SECRET_KEY" ]; then
  echo "SECRET_KEY is not set. Aborting."
  exit 1
fi

echo "🧱 Running database migrations..."
python manage.py migrate --noinput

echo "👑 Checking superuser..."

python manage.py shell << END
from django.contrib.auth import get_user_model
import os

User = get_user_model()
email = os.environ.get("DJANGO_SU_EMAIL")
password = os.environ.get("DJANGO_SU_PASSWORD")
username = os.environ.get("DJANGO_SU_NAME")

if not (email and password and username):
    print("❌ Missing DJANGO_SU_EMAIL, NAME or PASSWORD.")
else:
    if not User.objects.filter(email=email).exists():
        User.objects.create_superuser(username=username, email=email, password=password)
        print("✅ Superuser created:", email)
    else:
        print("ℹ️ Superuser already exists:", email)
END

echo "🧹 Collecting static files..."
python manage.py collectstatic --noinput

echo "🚀 Starting Gunicorn..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000
