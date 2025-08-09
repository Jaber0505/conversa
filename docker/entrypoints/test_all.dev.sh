#!/bin/bash
set -euo pipefail

# --- Params simples (modifiable à l'exécution) ---
REPORT_DIR="${REPORT_DIR:-/app/tests_reports}"
DJ_SETTINGS="${DJANGO_SETTINGS_MODULE:-config.settings.dev}"
TEST_TARGETS="${TEST_TARGETS:-*/tests}"   # cible tous les dossiers tests des apps
# -------------------------------------------------

echo "🧪 DEV • Lancement des tests"
echo "📜 Settings: ${DJ_SETTINGS}"
echo "🎯 Targets : ${TEST_TARGETS}"

# Se placer sur le backend
cd /app/backend
mkdir -p "${REPORT_DIR}"

# Versions utiles
echo ""
echo "0) Versions"
python - <<'PY'
import sys
print("Python", sys.version)
try:
    import django; print("Django", django.get_version())
except Exception as e:
    print("Django import error:", e)
PY

# Ruff (lint rapide, auto-fix safe)
echo ""
echo "1) Ruff (lint)…"
if command -v ruff >/dev/null 2>&1; then
  ruff check . --fix || true
else
  echo "⚠️ Ruff non installé (skip)."
fi

# Migrations (dev: on ne casse pas si rien à faire)
echo ""
echo "2) Migrations (dev)…"
export DJANGO_SETTINGS_MODULE="${DJ_SETTINGS}"
python manage.py makemigrations --check --dry-run || true
python manage.py migrate --noinput || true

# Pytest + Coverage (dev: pas de seuil, juste des rapports)
echo ""
echo "3) Pytest + Coverage (dev)…"
if ! command -v pytest >/dev/null 2>&1; then
  echo "❌ pytest manquant. Installe: pytest pytest-django pytest-cov pytest-html"
  exit 1
fi

pytest \
  -q \
  --junitxml="${REPORT_DIR}/junit.xml" \
  --cov=. \
  --cov-report=term-missing \
  --cov-report=xml:"${REPORT_DIR}/coverage.xml" \
  --cov-report=html:"${REPORT_DIR}/coverage_html" \
  --html="${REPORT_DIR}/tests_report.html" --self-contained-html \
  ${TEST_TARGETS}

echo ""
echo "✅ Terminé"
echo "📄 Tests HTML   : ${REPORT_DIR}/tests_report.html"
echo "📊 Coverage HTML: ${REPORT_DIR}/coverage_html/index.html"
echo "🧾 JUnit        : ${REPORT_DIR}/junit.xml"
