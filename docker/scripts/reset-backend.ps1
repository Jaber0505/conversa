Write-Host "Suppression des fichiers de migration..."
Get-ChildItem -Recurse -Include *.py,*.pyc -Exclude __init__.py -Filter migrations | Remove-Item -Force

Write-Host "Arret et suppression des containers + volumes..."
docker compose -f docker/compose.dev.yml down -v

Write-Host "Redemarrage des services..."
docker compose -f docker/compose.dev.yml up -d --build

Write-Host "Creation des migrations..."
docker compose -f docker/compose.dev.yml exec backend python manage.py makemigrations

Write-Host "Application des migrations..."
docker compose -f docker/compose.dev.yml exec backend python manage.py migrate

Write-Host "Reinitialisation terminee avec succes !"
