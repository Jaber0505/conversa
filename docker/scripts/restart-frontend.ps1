#!/usr/bin/env pwsh
Write-Host "Redemarrage du frontend uniquement"
docker compose -f docker/compose.dev.yml restart frontend
