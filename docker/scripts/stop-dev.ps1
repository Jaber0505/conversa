#!/usr/bin/env pwsh
Write-Host "Arret du projet en mode developpement (frontend + backend + db)"
docker compose -f docker/compose.dev.yml down
