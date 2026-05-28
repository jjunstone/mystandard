param(
  [int]$Port = 8000,
  [switch]$NoServer
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$LocalDeps = Join-Path $Root ".deps"
$BundledPython = "C:\Users\happy\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
$VenvConfig = Join-Path $Root ".venv\pyvenv.cfg"

if ($env:KQUANT_PYTHON) {
  $Python = $env:KQUANT_PYTHON
} elseif ((Test-Path $VenvPython) -and (Test-Path $VenvConfig)) {
  $Python = $VenvPython
} elseif (Test-Path $BundledPython) {
  $Python = $BundledPython
} else {
  $Python = "python"
}

if (Test-Path $LocalDeps) {
  $env:PYTHONPATH = "$LocalDeps;$Root;$env:PYTHONPATH"
} else {
  $env:PYTHONPATH = "$Root;$env:PYTHONPATH"
}

Set-Location $Root
& $Python scripts/import_free_data.py

if ($NoServer) {
  Write-Host "Snapshot updated. Refresh the dashboard."
  exit 0
}

$Existing = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($Existing) {
  Write-Host "Dashboard server already running: http://127.0.0.1:$Port/"
  Write-Host "Click REFRESH or IMPORT CSV in the dashboard."
  exit 0
}

Write-Host "Starting dashboard: http://127.0.0.1:$Port/"
& $Python -m uvicorn api.main:app --host 127.0.0.1 --port $Port
