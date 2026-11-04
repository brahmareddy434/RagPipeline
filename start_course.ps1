$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$env:COLLECTION_NAME = "course_hr_v2"
$env:TRACE_LOG_PATH = "course/results/ask_traces.jsonl"
& ".\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8001
