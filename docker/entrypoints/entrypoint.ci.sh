#!/bin/bash
set -e

echo "🔎 ENV_MODE=$ENV_MODE"
echo "📦 Using settings: $DJANGO_SETTINGS_MODULE"
echo "🧪 Python environment : $(python --version)"
echo "🗂️ Current directory : $(pwd)"
echo "📁 File contents :"
ls -la

echo "🔍 Checking for missing migrations..."
python manage.py makemigrations --check --dry-run

echo "🧱 Database migration..."
python manage.py migrate --noinput

echo "🔎 Code analysis with Ruff..."
ruff backend

echo "🧪 Execute unit tests with coverage..."
exec pytest --cov=backend --cov-report=term --cov-report=xml

echo "📤 Coverage report sent to Codecov..."