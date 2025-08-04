<#
  Usage: powershell -NoProfile -ExecutionPolicy Bypass ./stop.ps1
#>

$ErrorActionPreference = 'Continue'

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BaseCompose = Join-Path $ScriptDir '..\compose.base.yml' | Resolve-Path
$DevCompose  = Join-Path $ScriptDir '..\compose.dev.yml'  | Resolve-Path
$EnvFile     = Join-Path $ScriptDir '..\env\.env.dev'     | Resolve-Path

docker compose `
  --env-file $EnvFile `
  -f $BaseCompose `
  -f $DevCompose `
  down -v
