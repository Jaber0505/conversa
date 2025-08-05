#!/bin/bash
set -e

case "$ENV_MODE" in
  "ci")
    echo "✅ Running CI entrypoint"
    exec /entrypoint.ci.sh
    ;;
  "production")
    echo "🚀 Running production entrypoint"
    exec /entrypoint.prod.sh
    ;;
  "development")
    echo "🔧 Running dev server via manage.py"
    exec /entrypoint.dev.sh
    ;;
  *)
    echo "❌ Unknown or missing ENV_MODE: '$ENV_MODE'"
    echo "Please set ENV_MODE to one of: ci, production, development"
    exit 1
    ;;
esac
