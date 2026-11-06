# Week 02 - structured outputs and tools

Objective: W02-AC01–05, predictable JSON and a safe Python action. Reuse the schema-constrained Ollama client, bounded retries, calculator and fictional order lookup. New work adds React, a shared typed API client, `/api/v1` aliases and scoped access.

## Start

Prerequisites: existing Python environment, Ollama with the configured chat model, Node 24+, and `npm ci` inside `frontend`.

```powershell
# Root, terminal 1
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
# Terminal 2
cd frontend
npm run dev
```

Open http://127.0.0.1:5173/#/tools. Local mode accepts loopback only. Protected mode uses `ACCESS_MODE=authenticated` and `API_TOKEN_HASHES`, mapping token SHA-256 digests to `{tenant, role}`. Never commit plaintext tokens; the UI keeps a token only in memory.

## Mentor walkthrough

1. Submit **Calculate 2500 - 500**. Expected: `{"tool":"calculator","result":2000,"executed_by":"Python"}`. Python computes; the model chooses.
2. Ask **Where is ORD-1001?** for the existing fictional order lookup. Claims tools are a separate increment.
3. Inspect `POST /api/v1/tools/run` at `/docs`. Empty input returns 422; an unavailable provider returns 503. The UI shows errors and supports retry/cancellation.
4. Explain Pydantic validation and the restricted arithmetic parser: neither model output nor an expression can run arbitrary Python.
5. Show tenant/source/memory denial tests and `/course/results/...` returning 404. Private logs are no longer static assets.

## File purposes

| File | Purpose |
|---|---|
| `backend/app/config/settings.py` | Environment, token digests, roles, limits |
| `backend/app/controllers/tools.py` | HTTP translation |
| `backend/app/services/tools.py` | Tool selection and execution |
| `backend/app/domain/ports.py` | Small injectable interfaces |
| `backend/app/infrastructure/access.py` | Identity, permissions, origin checks, rate limit |
| `backend/app/controllers/dependencies.py` | Tenant-isolated store and trace dependencies |
| `frontend/src/lib/` | Shared HTTP/errors/cancellation |
| `frontend/src/features/tools/` | Accessible form and component tests |
| `tests/test_access.py` | Access and isolation regressions |

No relational migration; authenticated tenants get separate Chroma collections. Fresh continuation verification passed 176 backend tests, four frontend tests and the React production build. Further verification appears in `docs/architecture/completion-report.md`.

Limitations: token access is not enterprise OIDC, in-process rate limiting assumes one worker, and deployment needs TLS and approved real-data handling.

Talk track: “We preserved working tools, introduced a structured backend and React client, and made identity and validation explicit. The model cannot execute Python directly or choose its tenant.”
