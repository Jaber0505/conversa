# Active le venv, installe les dépendances et lance les tests
# Ajuste le chemin vers ton venv si besoin

# Activer le venv (Windows PowerShell)
& .\venv\Scripts\Activate.ps1

# Installer les dépendances
pip install -r backend/requirements/ci.txt

# Lancer les tests avec coverage
cd backend
pytest --cov=. --cov-report=term --cov-report=xml
