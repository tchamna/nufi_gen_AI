# Usage: .\scripts\run_app.ps1              # background, no auto-reload
#         .\scripts\run_app.ps1 -Reload    # background + --reload (Python file edits restart worker)
param(
    [switch]$Reload
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repoRoot ".venv\Scripts\python.exe"
$appPort = 8010
$logDir = Join-Path $repoRoot "logs"
$logFile = Join-Path $logDir "uvicorn.log"

if (-not (Test-Path $python)) {
    throw "Missing virtualenv python at $python"
}

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

# Kill listeners on this port only
try {
    $pids = Get-NetTCPConnection -LocalPort $appPort -State Listen -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($procId in $pids) {
        if ($procId -gt 0) {
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        }
    }
} catch {
}

try {
    $stale = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match "uvicorn\s+app:app" }
    foreach ($p in $stale) {
        if ($p.ProcessId -ne $PID) {
            Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
        }
    }
} catch {
}

Start-Sleep -Milliseconds 500

$uvArgs = @("-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", "$appPort")
if ($Reload) {
    $uvArgs += "--reload"
}

# Uvicorn logs to stderr — capture so crashes show up (Hidden window hides the console)
$proc = Start-Process -FilePath $python `
    -ArgumentList $uvArgs `
    -WorkingDirectory $repoRoot `
    -WindowStyle Hidden `
    -RedirectStandardError $logFile `
    -PassThru

Write-Output "Started app on http://127.0.0.1:$appPort with PID $($proc.Id)"
if ($Reload) {
    Write-Output "Auto-reload: ON (saving .py files restarts the worker; corpus/pickle changes still need a full restart)"
}
Write-Output "Logs: $logFile"
Write-Output "Tail logs: Get-Content -Path '$logFile' -Tail 40 -Wait"
Write-Output "Stop: Stop-Process -Id $($proc.Id) -Force"
