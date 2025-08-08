#!/usr/bin/env pwsh
Write-Host "Redemarrage du backend uniquement"
docker compose -f docker/compose.dev.yml restart backend
