#!/bin/bash
set -e

# ==============================================================================
# 🧪 Conversa – Entrypoint CI (tests unitaires locaux)
# ------------------------------------------------------------------------------
# Ce fichier est utilisé uniquement en LOCAL pour simuler le job CI :
# - Migrations
# - Tests unitaires
# - Lint
# - Génération de couverture
#
# ⚠️ Ce script N'EST PAS appelé par GitHub Actions.
# ⚠️ Il est inactif tant que non référencé (docker-compose, Dockerfile…)
#
# 👉 Pour l'exécuter localement :
#    docker compose -f docker/compose.ci.yml run --rm backend /entrypoints/entrypoint.ci.sh
# ==============================================================================

echo "🔎 ENV_MODE=$ENV_MODE"
echo "📦 DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-config.settings.ci}"
echo "🐍 Python: $(python --version)"
echo "📁 Working dir: $(pwd)"
echo "📂 Contents:"
ls -la

echo ""
echo "🔍 Vérification des migrations manquantes..."
python manage.py makemigrations --check --dry-run

echo ""
echo "🧱 Application des migrations..."
python manage.py migrate --noinput

echo ""
echo "🔎 Analyse statique du code (Ruff)..."
ruff backend || true  # Ne pas échouer même si Ruff échoue

echo ""
echo "🧪 Lancement des tests unitaires avec coverage..."
pytest --cov=backend --cov-report=term --cov-report=xml
