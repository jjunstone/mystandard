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
& $Python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
