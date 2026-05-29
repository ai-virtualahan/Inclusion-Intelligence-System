$ErrorActionPreference = "Stop"

$port = 5000
$processIds = @()

try {
    $connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction Stop
    $processIds = $connections | Select-Object -ExpandProperty OwningProcess -Unique
} catch {
    Write-Host "Could not inspect port $port with Get-NetTCPConnection. Trying netstat fallback..."
    $processIds = netstat -ano -p tcp |
        Select-String "LISTENING" |
        Where-Object { $_.Line -match "[:.]$port\s" } |
        ForEach-Object {
            $parts = $_.Line.Trim() -split "\s+"
            $parts[-1]
        } |
        Select-Object -Unique
}

foreach ($processId in $processIds) {
    if ($processId -and $processId -ne $PID) {
        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
        if ($process) {
            Write-Host "Stopping old Flask server on port $port (PID $processId)..."
            Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
        }
    }
}

$pythonPath = Join-Path $PSScriptRoot "venv\Scripts\python.exe"
if (-not (Test-Path $pythonPath)) {
    throw "Virtual environment Python was not found at $pythonPath"
}

$env:FLASK_DEBUG = "1"

Write-Host "Starting Inclusion Intelligence System on http://127.0.0.1:$port"
& $pythonPath (Join-Path $PSScriptRoot "app.py")
