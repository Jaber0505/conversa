#!/usr/bin/env pwsh
Write-Host "Suppression complete des containers, images, volumes"
docker compose -f docker/compose.dev.yml down -v --rmi all --remove-orphans
docker system prune -a -f
docker compose -f docker/compose.dev.yml up --build