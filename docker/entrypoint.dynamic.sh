#!/bin/bash
set -e

echo "🔁 CI_MODE=$CI_MODE"

if [ "$CI_MODE" = "true" ]; then
  echo "✅ Running CI entrypoint"
  exec /entrypoint.ci.sh
else
  echo "🚀 Running production entrypoint"
  exec /entrypoint.prod.sh
fi
