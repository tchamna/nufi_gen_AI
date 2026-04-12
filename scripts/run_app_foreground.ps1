# Runs uvicorn in this window — you see [startup] progress and errors (blocks until Ctrl+C).
# Default: --reload so edits to .py files pick up without manually restarting.
# Usage: .\scripts\run_app_foreground.ps1 -NoReload   # stable run, no file watching
param(
    [switch]$NoReload
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repoRoot ".venv\Scripts\python.exe"
$appPort = 8010

if (-not (Test-Path $python)) {
    throw "Missing virtualenv python at $python"
}

Set-Location $repoRoot
if ($NoReload) {
    & $python -m uvicorn app:app --host 127.0.0.1 --port $appPort
} else {
    Write-Host "[dev] --reload enabled: save a .py file to reload. Corpus/txt changes need a full restart." -ForegroundColor DarkCyan
    & $python -m uvicorn app:app --host 127.0.0.1 --port $appPort --reload
}
