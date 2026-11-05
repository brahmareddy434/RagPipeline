param(
    [switch]$Demo,
    [switch]$Live,
    [switch]$Serve,
    [switch]$List,
    [string]$Task = "What is the current status of claim CLM-2024-88120?"
)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$python = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if ($Serve) {
    & $python -m uvicorn app.main:app --host 127.0.0.1 --port 8003
} elseif ($Demo) {
    if ($Live) { & $python -m course.week9_demo --live }
    else { & $python -m course.week9_demo }
} elseif ($List) {
    & $python -m app.week9 --list
} elseif ($Live) {
    & $python -m app.week9 --task $Task
} else {
    & $python -m pytest tests/test_week9_mcp.py -q
}
exit $LASTEXITCODE
