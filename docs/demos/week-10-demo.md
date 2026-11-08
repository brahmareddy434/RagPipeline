# Week 10 mentor guide — race one agent against a small team

**Purpose:** Show a manager and two specialists, compare them with the single agent, and inspect measured quality, speed, tokens, cost and failure behavior.

- **Open the app:** `http://127.0.0.1:5173/#/demo/week10`
- **Important:** The saved race uses fictional Week-7/8 claims because the required ten Week-6 Task D claims and judge are not identified. It is provisional evidence, not a complete Week-6 submission.

## Before Week 10

One claims agent read the record, notes and clauses, then chose tools and wrote the answer. That is simple, but it gives one prompt the whole job. Our first live team sample also showed a risk: free-form synthesis attached a missing-estimate detail to the wrong numeric claim context and abstained.

## What we changed and why

We added one manager and two narrow specialists: coverage/exclusions and adjuster notes. They run concurrently on relevant read-only evidence. The manager checks exact source quotations and builds a grounded summary. We then raced that team against the original agent using identical questions and the same deterministic Week 8 judge. A separate injected 500 checks the failure path. We report the bill as well as the pass rate.

## Main files to show

| File | Status and reason |
|---|---|
| `backend/app/agents/claims_team.py` | **New:** manager, two narrow specialists, source checks and safe failure. |
| `backend/app/infrastructure/budgets.py`, `ollama.py` | **Updated:** reserve a shared budget and attribute provider usage. |
| `backend/app/controllers/claims.py`, `course/claims_team_race.py` | **Updated/new:** API routes; freezes inputs, applies the judge and writes reports. |
| `frontend/src/features/runs/Week10Demo.tsx` | **New:** shows the story, live runs and saved evidence. |
| `frontend/e2e/week10-demo.spec.ts`, `tests/test_claims_team.py`, `tests/test_provider_budget_reservations.py` | **New:** verify browser flow, failure safety, grounding and budget. |
| `requirements/week-10.md` | **New:** acceptance criteria and missing-cohort dependency. |
| `docs/demos/evidence/claims-team-race/<run-id>/` | **Evidence:** saved table, hand-off log, failure and verdict. |

## Start the frontend and backend

Use two PowerShell terminals at the repository root. Ollama and `llama3.2:3b` must be available. The fresh Chroma directory keeps demo data isolated.

**Terminal 1 — backend API**

```powershell
$env:CHROMA_PATH = 'data/week10-demo'
$env:COLLECTION_NAME = 'week10_demo_docs'
$env:MEMORY_COLLECTION_NAME = 'week10_demo_memory'
$env:TRACE_LOG_PATH = 'logs/week10-demo-traces.jsonl'
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**Terminal 2 — React frontend**

```powershell
Set-Location frontend
$env:API_PROXY_TARGET = 'http://127.0.0.1:8000'
npm run dev -- --host 127.0.0.1 --port 5173
```

Open `http://127.0.0.1:8000/docs` to show the backend API; the browser reaches it through the `/api` proxy.

## Show the mentor

1. Open **Week 10 live demo** and point out the cohort limitation.
2. Run the example question for `CLM-2026-10001` through both arms. Compare answer, tool steps, time, tokens and estimated cost. This single query is not judge-scored.
3. Select **Inject coverage worker 500**. Show the team reports a worker error, does not retry, and leaves coverage undetermined.
4. The saved ten-case race appears automatically. Open `race_table.md`, `handoffs.log`, `failure_case.md` and `verdict.md` on screen.
5. Open **Proposed AgentCard**. Explain this advertises the local agent; it does not mean a real A2A network endpoint exists.

The paired query endpoint is `POST /api/v1/claims/team/run`:

```json
{"claim_id":"CLM-2026-10001","arm":"both","task":"Summarize status and unresolved issues for CLM-2026-10001. Cite clauses; do not decide coverage."}
```

It returns `single` and `team` runs. `POST /api/v1/claims/team/race` makes a new ten-pair model run; it may take several minutes. `GET /api/v1/claims/team/race/latest` returns the saved report.

## Evidence and limits

Saved provisional race (single vs team): outcome proxy **0% vs 90%**; p50 **48.2s vs 18.9s**; p99 **70.1s vs 31.1s**; tokens **54,284 vs 6,780**; estimated cost **$0.001239 vs $0.000207 per claim**. Multiplier: **0.1x**; largest team hand-off: `manager->coverage_worker`, **53.2%** of team tokens. The injected 500 caused a safe abstention with no retry. Cost is a reference estimate, not an invoice.

This race used fictional Week-7/8 cases and the unchanged Week 8 assessor; the exact Week-6 set and judge remain missing, so W10-AC01 is pending. Validation: 218 backend tests, five React unit tests, production build and Week 10 Edge journey passed. Postman CLI was blocked by a private-cloud registry-policy error; the endpoint and saved-race API were checked directly.

## Simple talk track

“Before Week 10, one agent did every step. We added a manager with two focused helpers and measured whether that helped. On this provisional test, the team scored better and was faster, used fewer tokens, and had a lower estimated cost. When the coverage helper failed, the manager stopped safely. I still need the exact Week-6 claims questions and judge before I can call this the final required comparison.”
