#!/usr/bin/env pwsh
Write-Host "Activation de l’environnement virtuel local"

$venvPath = ".\venv\Scripts\Activate.ps1"

if (Test-Path $venvPath) {
    & $venvPath
} else {
    Write-Host "Aucun environnement virtuel trouvé à $venvPath"
}
