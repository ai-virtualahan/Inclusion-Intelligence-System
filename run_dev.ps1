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

try {
    $projectPath = (Resolve-Path $PSScriptRoot).Path
    $projectPythonPath = Join-Path $projectPath "venv\Scripts\python.exe"
    $stalePythonProcesses = Get-CimInstance Win32_Process -ErrorAction Stop |
        Where-Object {
            $_.CommandLine -and
            $_.CommandLine -match "(^|\\s|`")app\.py(`"|\\s|$)" -and
            (
                $_.CommandLine -like "*$projectPath*" -or
                $_.ExecutablePath -eq $projectPythonPath
            )
        }

    foreach ($staleProcess in $stalePythonProcesses) {
        if ($staleProcess.ProcessId -and $staleProcess.ProcessId -ne $PID) {
            Write-Host "Stopping stale Flask app.py process (PID $($staleProcess.ProcessId))..."
            Stop-Process -Id $staleProcess.ProcessId -Force -ErrorAction SilentlyContinue
        }
    }
} catch {
    Write-Host "Could not inspect stale app.py processes. Continuing with startup..."
}

$pythonPath = Join-Path $PSScriptRoot "venv\Scripts\python.exe"
if (-not (Test-Path $pythonPath)) {
    throw "Virtual environment Python was not found at $pythonPath"
}

$env:FLASK_DEBUG = "1"

Write-Host "Starting Inclusion Intelligence System on http://127.0.0.1:$port"
& $pythonPath (Join-Path $PSScriptRoot "app.py")
