param([int]$Port=8000,[switch]$BuildFrontend)
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    if (-not (Test-Path -LiteralPath '.venv/Scripts/python.exe')) { throw 'Create the Python environment using README.md first.' }
    if ($BuildFrontend) {
        Push-Location (Join-Path $projectRoot 'frontend')
        try { npm run build; if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' } }
        finally { Pop-Location }
    }
    & '.\.venv\Scripts\python.exe' -m uvicorn app.main:app --host 127.0.0.1 --port $Port
} finally { Pop-Location }
