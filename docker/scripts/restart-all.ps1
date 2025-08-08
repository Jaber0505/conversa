#!/usr/bin/env pwsh
Write-Host "Redemarrage des services"
docker compose -f docker/compose.dev.yml restart
