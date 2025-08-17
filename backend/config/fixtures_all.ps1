Param(
  [string]$ComposeFile = "docker/compose.dev.yml"
)

# 1) Lancer le backend (si pas déjà up)
docker compose -f $ComposeFile up -d backend

# 2) LANGUES
docker compose -f $ComposeFile exec backend python manage.py loaddata languages/fixtures/languages_min.json

# 3) USERS
docker compose -f $ComposeFile exec backend python manage.py loaddata users/fixtures/users.json

# 3) PARTENAIRES (unique condition: JSON non vide -> loaddata ; sinon -> script Python)
$partnersJson = "backend/partners/fixtures/partners.json"
if ((Test-Path $partnersJson) -and ((Get-Item $partnersJson).Length -gt 2)) {
  docker compose -f $ComposeFile exec backend python manage.py loaddata partners/fixtures/partners.json
} else {
  docker compose -f $ComposeFile exec backend python manage.py shell -c "exec(open('partners/fixtures/generate_partners.py','r',encoding='utf-8').read())"
}

# 4) EVENTS
docker compose -f $ComposeFile exec backend python manage.py loaddata events/fixtures/events.json

Write-Host "Fixtures chargees (langues -> utilisateurs -> partenaires -> events)."
