<#
.SYNOPSIS
    Load all Django fixtures in correct dependency order.

.DESCRIPTION
    This script loads fixtures for the Conversa application in the correct order
    to respect foreign key dependencies:
    1. Languages (no dependencies)
    2. Partners (no dependencies)
    3. Users (depends on languages)
    4. Events (depends on users, languages, partners)

.PARAMETER ComposeFile
    Path to docker-compose file. Default: docker/compose.dev.yml

.EXAMPLE
    .\load_fixtures.ps1
    .\load_fixtures.ps1 -ComposeFile docker/compose.prod.yml
#>

Param(
    [string]$ComposeFile = "docker/compose.dev.yml"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Loading Conversa Fixtures" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Ensure backend is running
Write-Host "[1/5] Starting backend container..." -ForegroundColor Yellow
docker compose -f $ComposeFile up -d backend

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to start backend container" -ForegroundColor Red
    exit 1
}

Write-Host "      Backend is ready" -ForegroundColor Green
Write-Host ""

# Load fixtures in dependency order
Write-Host "[2/5] Loading languages (12 languages)..." -ForegroundColor Yellow
docker compose -f $ComposeFile exec backend python manage.py loaddata 01_languages

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to load languages" -ForegroundColor Red
    exit 1
}

Write-Host "      Languages loaded" -ForegroundColor Green
Write-Host ""

Write-Host "[3/5] Loading partners (55 venues)..." -ForegroundColor Yellow
docker compose -f $ComposeFile exec backend python manage.py loaddata 02_partners

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to load partners" -ForegroundColor Red
    exit 1
}

Write-Host "      Partners loaded" -ForegroundColor Green
Write-Host ""

Write-Host "[4/5] Loading users (10 test users)..." -ForegroundColor Yellow
docker compose -f $ComposeFile exec backend python manage.py loaddata 03_users

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to load users" -ForegroundColor Red
    exit 1
}

Write-Host "      Users loaded" -ForegroundColor Green
Write-Host ""

Write-Host "[5/5] Loading events (sample events)..." -ForegroundColor Yellow
docker compose -f $ComposeFile exec backend python manage.py loaddata 04_events

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to load events" -ForegroundColor Red
    exit 1
}

Write-Host "      Events loaded" -ForegroundColor Green
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  All fixtures loaded successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Summary:"
Write-Host "  - 12 languages"
Write-Host "  - 55 partner venues"
Write-Host "  - 10 test users"
Write-Host "  - Sample events"
Write-Host ""
