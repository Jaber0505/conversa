#!/bin/bash
set -e

echo "ENV_MODE=$ENV_MODE"

case "$ENV_MODE" in
  "ci")
    echo "✅ Running CI entrypoint"
    exec /entrypoint.ci.sh
    ;;
  "production")
    echo "🚀 Running production entrypoint"
    exec /entrypoint.prod.sh
    ;;
  *)
    echo "❌ Unknown or missing ENV_MODE: '$ENV_MODE'"
    echo "Please set ENV_MODE to one of: ci, production"
    exit 1
    ;;
esac
