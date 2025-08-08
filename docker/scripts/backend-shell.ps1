#!/usr/bin/env pwsh
Write-Host "Acces au shell du conteneur backend"
docker compose -f docker/compose.dev.yml exec backend bash
