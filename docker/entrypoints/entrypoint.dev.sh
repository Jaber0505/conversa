#!/bin/bash
set -e

echo "🔧 ENV_MODE=$ENV_MODE"
echo "📦 Using settings: $DJANGO_SETTINGS_MODULE"
echo "🐘 Connecting to DB at: $DJANGO_DB_HOST:$DJANGO_DB_PORT"

# Appliquer automatiquement les migrations (utile en dev)
echo "🧱 Making migrations if needed..."
python manage.py makemigrations --noinput

echo "⚙️ Applying migrations..."
python manage.py migrate --noinput

# Créer un superuser si aucun n'existe déjà (optionnel)
echo "👑 Creating superuser if needed..."
python manage.py shell << END
from django.contrib.auth import get_user_model
from datetime import date
User = get_user_model()
if not User.objects.filter(email='${DJANGO_SU_EMAIL}').exists():
    User.objects.create_superuser(
        email='${DJANGO_SU_EMAIL}',
        password='${DJANGO_SU_PASSWORD}',
        first_name='Admin',
        last_name='User',
        birth_date=date(1990, 1, 1),  # ← requis
        language_native='fr'          # ← requis
    )
END


# Lancer le serveur
echo "🚀 Launching Django dev server at http://0.0.0.0:8000"
exec python manage.py runserver 0.0.0.0:8000
