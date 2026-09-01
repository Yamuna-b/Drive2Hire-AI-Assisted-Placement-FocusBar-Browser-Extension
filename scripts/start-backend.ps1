$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
  Write-Error "Virtual env not found. Run: python -m venv .venv; .\.venv\Scripts\pip install -r backend\requirements.txt"
}

$port = 8000
$inUse = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue

if ($inUse) {
  $processId = $inUse[0].OwningProcess
  try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:$port/health" -TimeoutSec 2
    Write-Host "Backend already running on http://127.0.0.1:$port (PID $processId)"
    Write-Host "Health: $($health | ConvertTo-Json -Compress)"
    Write-Host ""
    Write-Host "To restart, stop the old server first:"
    Write-Host "  Stop-Process -Id $processId -Force"
    exit 0
  } catch {
    Write-Host "Port $port is in use by PID $processId but it is not the Placement FocusBar API."
    Write-Host "Free the port or run on another port:"
    Write-Host "  .\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8001 --reload"
    exit 1
  }
}

Write-Host "Starting Placement FocusBar backend on http://127.0.0.1:$port"
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port $port --reload
