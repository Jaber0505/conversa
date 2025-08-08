#!/usr/bin/env bash
set -e

cd /app/backend
echo "🌍 DEV | Settings=${DJANGO_SETTINGS_MODULE:-config.settings.dev}"

# 1) Migrations (idempotentes)
python manage.py migrate --noinput || true

# 2) Superuser si variables présentes (sinon skip)
if [ -n "${DJANGO_SU_EMAIL:-}" ] && [ -n "${DJANGO_SU_PASSWORD:-}" ]; then
python <<'PY'
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.getenv("DJANGO_SETTINGS_MODULE","config.settings.dev"))
django.setup()
from django.contrib.auth import get_user_model
from datetime import date
U = get_user_model()
email = os.getenv("DJANGO_SU_EMAIL")
pwd   = os.getenv("DJANGO_SU_PASSWORD")
if not U.objects.filter(email=email).exists():
    U.objects.create_superuser(email=email, password=pwd, first_name="Admin", last_name="User", birth_date=date(1990,1,1), language_native="fr")
    print(f"✅ Superuser created: {email}")
else:
    print(f"✅ Superuser already present: {email}")
PY
else
  echo "ℹ️  No DJANGO_SU_EMAIL/PASSWORD provided (skip superuser)"
fi

# 3) Serveur dev sans doublons de logs (autre que runserver)
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 1 --threads 4 --timeout 120 --reload
