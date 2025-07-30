echo "📦 Applying Django migrations..."
python manage.py migrate --noinput

if [ "$ENV_MODE" = "production" ]; then
  echo "🧹 Collecting static files..."
  python manage.py collectstatic --noinput --clear
fi

echo "🚀 Starting Gunicorn..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000
