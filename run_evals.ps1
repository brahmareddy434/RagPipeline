<#
  Week 6 Task Set C — one command per step, in the order the blind protocol requires.

    .\run_evals.ps1                 # score the saved answers, pass rate BY MODE
    .\run_evals.ps1 -Regenerate     # answer the live cases first, then score  (needs Ollama)
    .\run_evals.ps1 -Label          # blind hand-labelling of 25 answers  (you label)
    .\run_evals.ps1 -Agreement      # judge v1 -> v2, agreement before/after  (needs Ollama)
    .\run_evals.ps1 -Status         # is the label seal intact?
    .\run_evals.ps1 -Tests          # offline unit tests, no Ollama needed
    .\run_evals.ps1 -Check          # as default, but non-zero exit if a mode is below 100%

  The order matters and the tools enforce it: -Agreement refuses to run until the labels
  are sealed, and refuses again if they changed afterwards.
#>
param(
    [switch]$Regenerate,
    [switch]$Label,
    [switch]$Agreement,
    [switch]$Status,
    [switch]$Tests,
    [switch]$Check
)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Create the virtual environment first: py -3.11 -m venv .venv; .\.venv\Scripts\python.exe -m pip install -r requirements.txt" }

if ($Tests)           { & $python -m pytest -q }
elseif ($Label)       { & $python -m evaluation.week6.label_blind }
elseif ($Status)      { & $python -m evaluation.week6.label_blind --status }
elseif ($Agreement)   { & $python -m evaluation.week6.agreement }
elseif ($Regenerate)  { & $python -m evaluation.week6.run_evals --regenerate }
elseif ($Check)       { & $python -m evaluation.week6.run_evals --check }
else                  { & $python -m evaluation.week6.run_evals }
exit $LASTEXITCODE
