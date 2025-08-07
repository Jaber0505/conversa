Write-Host "Arret des containers..."
docker stop conversa-frontend-1 conversa-backend-1 conversa-db-1 conversa-pgadmin-1 db 2>$null

Write-Host "Suppression des containers..."
docker rm conversa-frontend-1 conversa-backend-1 conversa-db-1 conversa-pgadmin-1 db 2>$null

Write-Host "Suppression des volumes..."
docker volume rm conversa_postgres_data conversa_pgadmin_data docker_postgres_data_ci 2>$null

Write-Host "Reconstruction et relance..."
docker compose -f docker/compose.dev.yml up -d --build

Write-Host "Attente initialisation PostgreSQL..."
Start-Sleep -Seconds 8
docker compose -f docker/compose.dev.yml exec db psql -U conversa_user -l
