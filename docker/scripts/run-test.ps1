#!/usr/bin/env pwsh
Write-Host "Execution complete des tests (via test_all.sh)"
docker compose -f docker/compose.dev.yml exec backend bash /entrypoints/test_all.sh
