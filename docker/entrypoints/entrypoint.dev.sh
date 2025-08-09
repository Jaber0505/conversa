#!/usr/bin/env bash
set -euo pipefail

# Defaults DEV
export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-config.settings.dev}"
export PYTHONPATH="${PYTHONPATH:-/app/backend}"
REPORT_DIR="${REPORT_DIR:-/app/tests_reports}"
TEST_TARGETS="${TEST_TARGETS:-*/tests}"     # ex: "users/tests" ou "*/tests"
RUN_TESTS="${RUN_TESTS:-0}"                 # 0 = normal, 1 = lancer les tests et sortir

cd /app/backend
echo "🌍 DEV | Settings=${DJANGO_SETTINGS_MODULE}"
mkdir -p "${REPORT_DIR}"

# 1) Migrations (idempotent)
python manage.py migrate --noinput || true

# 2) Superuser si variables présentes (facultatif)
if [ -n "${DJANGO_SU_EMAIL:-}" ] && [ -n "${DJANGO_SU_PASSWORD:-}" ]; then
python <<'PY'
import os, django
from datetime import date
os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.getenv("DJANGO_SETTINGS_MODULE","config.settings.dev"))
django.setup()
from django.contrib.auth import get_user_model
U = get_user_model()
email = os.getenv("DJANGO_SU_EMAIL"); pwd = os.getenv("DJANGO_SU_PASSWORD")
if not U.objects.filter(email=email).exists():
    U.objects.create_superuser(email=email, password=pwd, first_name="Admin", last_name="User", birth_date=date(1990,1,1), language_native="fr")
    print(f"✅ Superuser created: {email}")
else:
    print(f"✅ Superuser already present: {email}")
PY
else
  echo "ℹ️  Pas de DJANGO_SU_EMAIL/PASSWORD (skip superuser)"
fi

# 3) Mode tests on-demand
if [ "${RUN_TESTS}" = "1" ]; then
  echo "🧪 DEV TESTS | Targets=${TEST_TARGETS}"

  # Ruff (auto-fix safe)
  if command -v ruff >/dev/null 2>&1; then
    echo "🔎 Ruff…"
    ruff check . --fix || true
  else
    echo "⚠️ Ruff non installé (skip)"
  fi

  # Pytest + Coverage (dev : pas de seuil, pas de config externe)
  if ! command -v pytest >/dev/null 2>&1; then
    echo "❌ pytest manquant. Installe: pytest pytest-django pytest-cov pytest-html"
    exit 1
  fi

  echo "▶️  pytest…"
  pytest -q \
    --cov=. \
    --cov-report=term-missing \
    --cov-report=xml:"${REPORT_DIR}/coverage.xml" \
    --cov-report=html:"${REPORT_DIR}/coverage_html" \
    --junitxml="${REPORT_DIR}/junit.xml" \
    --html="${REPORT_DIR}/tests_report.html" --self-contained-html \
    ${TEST_TARGETS}

  echo "✅ Tests terminés"
  echo "📄 Tests HTML   : ${REPORT_DIR}/tests_report.html"
  echo "📊 Coverage HTML: ${REPORT_DIR}/coverage_html/index.html"
  echo "🧾 JUnit        : ${REPORT_DIR}/junit.xml"
  exit 0
fi

# 4) Serveur dev (gunicorn --reload pour pas de doublons logs)
echo "🚀 DEV server…"
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 1 --threads 4 --timeout 120 --reload
