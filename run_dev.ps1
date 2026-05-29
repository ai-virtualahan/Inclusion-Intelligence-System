$ErrorActionPreference = "Stop"

$port = 5000
$connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
$processIds = $connections | Select-Object -ExpandProperty OwningProcess -Unique

foreach ($processId in $processIds) {
    if ($processId -and $processId -ne $PID) {
        Write-Host "Stopping old Flask server on port $port (PID $processId)..."
        Stop-Process -Id $processId -Force
    }
}

$pythonPath = Join-Path $PSScriptRoot "venv\Scripts\python.exe"
if (-not (Test-Path $pythonPath)) {
    throw "Virtual environment Python was not found at $pythonPath"
}

Write-Host "Starting Inclusion Intelligence System on http://127.0.0.1:$port"
& $pythonPath (Join-Path $PSScriptRoot "app.py")
