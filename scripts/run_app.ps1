$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repoRoot ".venv\Scripts\python.exe"
$appPort = 8010
$targetPorts = (8000..8005) + $appPort

if (-not (Test-Path $python)) {
    throw "Missing virtualenv python at $python"
}

$listenerPids = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
    Where-Object { $_.LocalPort -in $targetPorts } |
    Select-Object -ExpandProperty OwningProcess -Unique

foreach ($listenerProcId in $listenerPids) {
    try {
        Stop-Process -Id $listenerProcId -Force
    } catch {
    }
}

$stalePids = Get-CimInstance Win32_Process |
    Where-Object { $_.CommandLine -match "-m uvicorn app:app" -and $_.ProcessId -ne $PID } |
    Select-Object -ExpandProperty ProcessId -Unique

foreach ($staleProcId in $stalePids) {
    try {
        Stop-Process -Id $staleProcId -Force
    } catch {
    }
}

Start-Sleep -Seconds 1

$process = Start-Process -FilePath $python `
    -ArgumentList "-m", "uvicorn", "app:app", "--host", "127.0.0.1", "--port", "$appPort" `
    -WorkingDirectory $repoRoot `
    -PassThru

Write-Output "Started app on http://127.0.0.1:$appPort with PID $($process.Id)"
