<#
  Week 8 Task Set C — one command per deliverable.

    .\run_week8.ps1                      # offline unit tests, no Ollama needed
    .\run_week8.ps1 -Before               # trajectory eval, pre-mitigation budget (max_steps=6)
    .\run_week8.ps1 -After                # trajectory eval, post-mitigation budget (max_steps=4)
    .\run_week8.ps1 -Compare              # before/after regression table
    .\run_week8.ps1 -Attack               # re-run only the injection case (q11) against current code
    .\run_week8.ps1 -Serve                # API + the /agent screen on port 8002, Week 8 corpus
#>
param(
    [switch]$Before,
    [switch]$After,
    [switch]$Compare,
    [switch]$Attack,
    [switch]$Serve
)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Create the virtual environment first: py -3.11 -m venv .venv; .\.venv\Scripts\python.exe -m pip install -r requirements.txt" }

if ($Serve) {
    $env:COLLECTION_NAME = "course_week8_handbook"
    $env:TRACE_LOG_PATH = "course/results/agent_traces.jsonl"
    Write-Host "Agent screen: http://127.0.0.1:8002/agent" -ForegroundColor Cyan
    Write-Host "Swagger:      http://127.0.0.1:8002/docs" -ForegroundColor Cyan
    & $python -m uvicorn app.main:app --host 127.0.0.1 --port 8002
}
elseif ($Before) {
    & $python -m course.trajectory_eval --tag before --max-steps 6
}
elseif ($After) {
    & $python -m course.trajectory_eval --tag after --max-steps 4
}
elseif ($Compare) {
    & $python -m course.trajectory_eval --compare before after
}
elseif ($Attack) {
    & $python -m course.trajectory_eval --tag attack_live --only q11_injection_manager_comment --max-steps 4
}
else {
    & $python -m pytest tests/test_agent.py tests/test_answer_quality.py -q
}
exit $LASTEXITCODE
