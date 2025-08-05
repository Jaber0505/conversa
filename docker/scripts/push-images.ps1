# Variables à adapter
$githubUser = "Jaber0505"               # Ton nom d'utilisateur GitHub ou organisation
$repoName = "conversa"                  # Nom du dépôt GitHub

# Tags locaux des images (selon ta convention locale)
$localBackendImage = "conversa-backend-local"
$localFrontendImage = "conversa-frontend-local"

# Tags GHCR (latest ou tag spécifique)
$remoteBackendImage = "ghcr.io/$githubUser/$repoName-backend:latest"
$remoteFrontendImage = "ghcr.io/$githubUser/$repoName-frontend:latest"

Write-Host "🔑 Login à GitHub Container Registry (GHCR)..."
docker login ghcr.io

Write-Host "🔖 Tag de l'image backend locale pour GHCR..."
docker tag $localBackendImage $remoteBackendImage

Write-Host "🔖 Tag de l'image frontend locale pour GHCR..."
docker tag $localFrontendImage $remoteFrontendImage

Write-Host "📤 Push de l'image backend vers GHCR..."
docker push $remoteBackendImage

Write-Host "📤 Push de l'image frontend vers GHCR..."
docker push $remoteFrontendImage

Write-Host "✅ Push des images Docker terminé."
