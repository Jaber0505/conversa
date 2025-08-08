#!/usr/bin/env bash
set -e
cd /app
echo "🚦 CI | Settings=${DJANGO_SETTINGS_MODULE:-config.settings.ci} | Python=$(python --version)"
chmod +x /entrypoints/test_all.sh
exec /entrypoints/test_all.sh
