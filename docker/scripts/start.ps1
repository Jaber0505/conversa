<#
  Usage: 
  powershell -NoProfile -ExecutionPolicy Bypass ./start.ps1
#>

$ErrorActionPreference = 'Stop'

# Répertoire absolu du script (docker/scripts)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Fichiers Compose et .env dans docker/
$BaseCompose = Join-Path $ScriptDir '..\compose.base.yml'
$DevCompose  = Join-Path $ScriptDir '..\compose.dev.yml'
$EnvFile     = Join-Path $ScriptDir '..\env\.env.dev'

Write-Host "Subnetwork = 'conversa'; using env-file = $EnvFile"

# Créer le réseau Docker si besoin (ignore l'erreur s’il existe déjà)
try {
    docker network inspect conversa | Out-Null
}
catch {
    Write-Host "Creating Docker network 'conversa'"
    docker network create conversa | Out-Null
}

# Lancer docker compose avec interpolation des variables via .env
docker compose `
  --env-file $EnvFile `
  -f $BaseCompose `
  -f $DevCompose `
  up --build
