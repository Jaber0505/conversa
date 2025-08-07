Write-Host "Rebuild complet des services Docker (sans cache)..."

docker compose -f docker/compose.dev.yml down --volumes --remove-orphans

docker compose -f docker/compose.dev.yml build --no-cache

docker compose -f docker/compose.dev.yml up --detach

Write-Host "Rebuild termine. Les conteneurs sont relances en arriere-plan."