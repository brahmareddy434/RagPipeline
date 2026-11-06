# Insurance Claims RAG Workbench

A local training application for Weeks 01-09: FastAPI, Ollama, Chroma, configurable MCP servers and a React workbench. It uses fictional claims fixtures and demonstrates evidence-grounded triage; it never authorizes coverage decisions or payments. The project is implemented and tested locally. Human review, real claims/provider inputs and peer acceptance remain explicit external requirements.

- [Weekly acceptance and verification map](docs/architecture/traceability.md)
- [Execution report and measured limitations](docs/architecture/completion-report.md)
- [Week-by-week mentor demos](docs/demos/README.md)
- [Weekly requirements](requirements/README.md)
- [API and Postman smoke checks](docs/api/README.md)

## Start locally

Prerequisites: Windows PowerShell, Python 3.11, Node/npm, Ollama, and the models configured in `.env.example`.

```powershell
ollama serve
# In another terminal, install the configured local models:
ollama pull llama3.2:3b
ollama pull nomic-embed-text:latest

py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env } else { Write-Host '.env already exists; keeping it.' }

cd frontend
npm ci
npm run build
cd ..
.\scripts\start-local.ps1
```

Open `http://127.0.0.1:8000/` for React and `/docs` for the API. Update `.env` if Ollama uses a different URL or model. Local access mode is for a single-user training environment; it is not production identity or tenant isolation.

## Workbench

The React application includes structured tools, document upload/source management, grounded policy Q&A, retrieval inspection, redacted traces, deterministic evaluation, agent-vs-workflow comparison, trajectory benchmarks and MCP discovery/run traces. Long-running model requests show their budgets, steps, citations and stop reason.

Backend source lives in `backend/app`, organized by domain, controllers, services, agents, RAG, repositories and infrastructure. The root `app/` package preserves historical imports. `course/` contains training exercises and explicitly fictional claims data. `docs/demos/evidence/` keeps dated experiment artifacts, including partial runs; do not overwrite them. `frontend/` contains the React application.

## Verify

```powershell
.\.venv\Scripts\python.exe -m pytest -q --tb=short
cd frontend
npm test
npm run build
npx playwright test e2e/claims-pages.spec.ts
```

The two browser tests above use mocked claim responses for the comparison/MCP pages. The full live browser journeys in `frontend/e2e/journeys.spec.ts` additionally call the local Ollama model. The read-only API contract smoke collection is `docs/postman/Claims_Workbench.postman_collection.json`.

Local experiment scores use assistant-authored fictional cases and, where noted, model-estimated costs. Real adjuster questions, authentic traces, human labels and peer calls are not included. See each week's requirement and demo before interpreting a result.

## Data and safety boundary

Keep `.env`, `.venv`, `data/`, `uploads/`, `logs/` and the ignored `backups/` directory local. Do not place real claimant data into this training app. Historical HR materials stay labeled as HR evidence and are not claims acceptance. Real-data deployment needs reviewed identity, authorization, redaction/retention, scoped tools, request budgets and restricted static files.
