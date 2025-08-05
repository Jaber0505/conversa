# Stopper le script en cas d'erreur
$ErrorActionPreference = "Stop"

# Se placer dans le dossier backend
Set-Location ./backend

# Vérifie si le dossier venv existe déjà
if (-Not (Test-Path -Path ".\venv")) {
    Write-Host "Creation de l'environnement virtuel dans le dossier backend..."
    python -m venv venv
    Write-Host "Environnement virtuel cree avec succes."
} else { Write-Host "L'environnement virtuel existe deja."}

# Activer l'environnement virtuel
Write-Host "Activation de l'environnement virtuel..."
& "$PWD\venv\Scripts\Activate.ps1"

# Mettre à jour pip
Write-Host "Mise a jour de pip..."
python -m pip install --upgrade pip

# Installer les dépendances
Write-Host "Installation des dependances..."
pip install -r requirements/ci.txt

# Lancer les tests avec coverage
Write-Host "Lancement des tests avec coverage..."
pytest --cov=. --cov-report=term --cov-report=xml
