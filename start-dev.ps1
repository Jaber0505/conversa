# start-dev.ps1

Write-Host "Restarting Docker services with build..."

docker compose down --remove-orphans
docker compose build
docker compose up
