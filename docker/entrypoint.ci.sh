#!/bin/bash
set -e

echo "Running CI tests..."

python manage.py migrate --noinput
exec pytest --cov
