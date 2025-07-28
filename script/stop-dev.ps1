# stop-dev.ps1
Write-Host "🛑 Stop Docker services..."

docker compose down --remove-orphans
