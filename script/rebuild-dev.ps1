# rebuild-dev.ps1
Write-Host "Rebuilding Docker images and restarting..."

docker compose down --remove-orphans
docker compose build
docker compose up
