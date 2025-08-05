#!/bin/bash
set -e

echo "🔧 [DEV] Starting Django development server..."
echo "📦 Using settings: $DJANGO_SETTINGS_MODULE"
echo "🐘 Connecting to DB at: $DJANGO_DB_HOST:$DJANGO_DB_PORT"

# Attendre que la DB soit prête (juste au cas où)
echo "⏳ Waiting for PostgreSQL to be ready..."
while ! pg_isready -h "$DJANGO_DB_HOST" -p "$DJANGO_DB_PORT" -U "$DJANGO_DB_USER" > /dev/null 2>&1; do
  sleep 1
done
echo "✅ PostgreSQL is ready."

# Appliquer automatiquement les migrations (utile en dev)
echo "⚙️ Applying migrations..."
python manage.py migrate --noinput

# Créer un superuser si aucun n'existe déjà (optionnel)
echo "👑 Creating superuser if needed..."
python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='${DJANGO_SU_NAME}').exists():
    User.objects.create_superuser(
        username='${DJANGO_SU_NAME}',
        email='${DJANGO_SU_EMAIL}',
        password='${DJANGO_SU_PASSWORD}'
    )
END

# Lancer le serveur
echo "🚀 Launching Django dev server at http://0.0.0.0:8000"
exec python manage.py runserver 0.0.0.0:8000
