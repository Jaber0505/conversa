#!/usr/bin/env pwsh
Write-Host "Rebuild complet des services"
docker compose -f docker/compose.dev.yml down --remove-orphans
docker compose -f docker/compose.dev.yml build --no-cache
docker compose -f docker/compose.dev.yml up --build
