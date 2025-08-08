#!/usr/bin/env pwsh
Write-Host "Redemarrage du backend..."
docker compose -f docker/compose.dev.yml build backend
Write-Host "Recreation du container backend..."
docker compose -f docker/compose.dev.yml up --no-cache backend
Write-Host "Backend redemarre avec succes."