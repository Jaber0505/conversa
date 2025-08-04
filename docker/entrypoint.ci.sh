#!/bin/sh
set -e

echo "📦 CI : Applying migrations"
python manage.py migrate --noinput

echo "✅ CI : Running tests"
python manage.py test
