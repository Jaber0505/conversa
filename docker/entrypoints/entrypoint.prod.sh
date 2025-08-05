#!/bin/bash
set -e

echo "🌍 ENV_MODE=$ENV_MODE"
echo "📦 DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE"

# Vérification de la clé secrète
if [ -z "$SECRET_KEY" ]; then
  echo "❌ SECRET_KEY is not set. Aborting."
  exit 1
fi

echo "🧱 Running database migrations..."
python manage.py migrate --noinput --verbosity 2

echo "🔍 Vérification des migrations..."
if python manage.py showmigrations --plan | grep "\[ \]"; then
  echo "❌ Certaines migrations ne sont pas appliquées. Abandon."
  exit 1
else
  echo "✅ Toutes les migrations sont appliquées."
fi

echo "👑 Vérification du superutilisateur..."

python manage.py shell -c "
from django.contrib.auth import get_user_model
import os

User = get_user_model()
email = os.environ.get('DJANGO_SU_EMAIL')
password = os.environ.get('DJANGO_SU_PASSWORD')
username = os.environ.get('DJANGO_SU_NAME')

try:
    if not User.objects.filter(email=email).exists():
        User.objects.create_superuser(username=username, email=email, password=password)
        print(f'✅ Superuser créé : {email}')
    else:
        print(f'ℹ️ Superuser déjà existant : {email}')
except Exception as e:
    print('❌ Erreur lors de la vérification/création du superuser :', e)
    import sys
    sys.exit(1)
"

echo "🧹 Collecting static files..."
python manage.py collectstatic --noinput

echo "🚀 Starting Gunicorn..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000
