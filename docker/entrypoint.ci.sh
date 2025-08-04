#!/bin/sh
set -e

echo "📦 Checking migrations plan..."
python manage.py showmigrations --plan || echo "🔍 Migrations check failed"

echo "🛠️ Applying migrations..."
python manage.py migrate --noinput

echo "🧪 Running tests..."
python manage.py test
