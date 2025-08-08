#!/usr/bin/env pwsh
Write-Host "Lancement du projet en mode developpement (frontend + backend + db)"
docker compose -f docker/compose.dev.yml up --build
