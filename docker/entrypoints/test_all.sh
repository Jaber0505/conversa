#!/bin/bash
set -euo pipefail

REPORT_DIR="backend/tests_reports"
COV_MIN="${COV_MIN:-80}"
DJ_SETTINGS="${DJANGO_SETTINGS_MODULE:-config.settings.ci}"

echo "🧪 Lancement des tests"
echo "🌍 ENV_MODE=${ENV_MODE:-ci}"
echo "📜 Settings: ${DJ_SETTINGS}"

# Se placer sur le projet
cd /app/backend
echo "📂 Dossier de travail: $(pwd)"

# Dossier de rapports
mkdir -p "${REPORT_DIR}"

# 0) Versions utiles
echo ""
echo "0. Versions"
python -c "import sys, django; print('Python', sys.version); print('Django', django.get_version())" || true

# 1) Lint (Ruff)
echo ""
echo "1. Analyse statique avec Ruff..."
if command -v ruff >/dev/null 2>&1; then
  ruff check . --fix || true
else
  echo "⚠️ Ruff non installé (skip)."
fi

# 2) Vérif migrations manquantes (échec si manquantes)
echo ""
echo "2. Vérification des migrations manquantes..."
python manage.py makemigrations --check --dry-run

# 3) Migrations
echo ""
echo "3. Application des migrations..."
python manage.py migrate --noinput

# 4) Validation OpenAPI (schema dans les rapports)
echo ""
echo "4. Validation de la documentation OpenAPI..."
python manage.py spectacular --validate --file "${REPORT_DIR}/openapi_schema.yml"

# 5) Tests + couverture + rapports (JUnit/XML/HTML)
echo ""
echo "5. Tests unitaires avec couverture..."
if ! command -v pytest >/dev/null 2>&1; then
  echo "❌ pytest introuvable. Installe pytest/pytest-django/pytest-cov dans requirements/ci.txt."
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
  --cov-fail-under="${COV_MIN}"

# 6) Résumé
echo ""
echo "📄 Rapport tests HTML : ${REPORT_DIR}/tests_report.html"
echo "📊 Couverture HTML    : ${REPORT_DIR}/coverage_html/index.html"
echo "🧾 JUnit              : ${REPORT_DIR}/junit.xml"
echo "📜 OpenAPI schema     : ${REPORT_DIR}/openapi_schema.yml"
