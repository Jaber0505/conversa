# .\scripts\switch-env.ps1 local
# .\scripts\switch-env.ps1 prod
param (
    [Parameter(Mandatory=$true)]
    [ValidateSet("local", "prod")]
    [string]$env
)

$envFilePath = "..\backend\.env"

if ($env -eq "local") {
    Copy-Item "..\backend\.env.local" $envFilePath -Force
    Write-Host "✅ Environnement local activé (.env ← .env.local)" -ForegroundColor Green
}
elseif ($env -eq "prod") {
    Copy-Item "..\backend\.env.prod" $envFilePath -Force
    Write-Host "✅ Environnement production activé (.env ← .env.prod)" -ForegroundColor Yellow
}
