<#
  Week 7 Task Set C — one command per deliverable.

    .\run_week7.ps1                      # offline unit tests, no Ollama needed
    .\run_week7.ps1 -Race                # the race: 10 questions, both systems, race.csv
    .\run_week7.ps1 -Race -Repeats 2
    .\run_week7.ps1 -BudgetDemo          # force a clean budget termination and log it
    .\run_week7.ps1 -BudgetDemo max_cost_usd
    .\run_week7.ps1 -Tools               # print the tool catalogue the model actually sees
    .\run_week7.ps1 -Serve               # API + the /agent screen on port 8001
#>
param(
    [switch]$Race,
    [switch]$Serve,
    [switch]$Tools,
    [string]$BudgetDemo,
    [int]$Repeats = 1,
    [int]$MaxSteps = 6
)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Create the virtual environment first: py -3.11 -m venv .venv; .\.venv\Scripts\python.exe -m pip install -r requirements.txt" }

if ($Serve) {
    $env:COLLECTION_NAME = "course_week7_handbook"
    $env:TRACE_LOG_PATH = "course/results/agent_traces.jsonl"
    Write-Host "Agent screen: http://127.0.0.1:8001/agent" -ForegroundColor Cyan
    & $python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
}
elseif ($Tools) {
    & $python -c "from app.agents.tools import ToolRegistry; from app.services.tools import Calculator; print(ToolRegistry(None, Calculator()).catalogue())"
}
elseif ($BudgetDemo) {
    & $python -m course.race --budget-demo $BudgetDemo
}
elseif ($PSBoundParameters.ContainsKey('BudgetDemo')) {
    & $python -m course.race --budget-demo
}
elseif ($Race) {
    & $python -m course.race --repeats $Repeats --max-steps $MaxSteps
}
else {
    & $python -m pytest tests/test_agent.py tests/test_week6_week7.py -q
}
exit $LASTEXITCODE
