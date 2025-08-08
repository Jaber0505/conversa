#!/usr/bin/env pwsh
Write-Host "Logs temps reel (tous services)"
docker compose -f docker/compose.dev.yml logs -f
