# Week 8 mentor guide — check the answer and the path

**Purpose:** Show how the claims agent behaved before Week 8, the one change made in Week 8, and what the saved evidence proves.

- **Open the app:** `http://127.0.0.1:5173/#/demo/week8`
- **Benchmark screen:** `http://127.0.0.1:5173/#/benchmarks`

## Before Week 8

The earlier claims agent could read claim records, adjuster notes and policy clauses. It chose tool names and arguments itself. In the ten-case baseline, it combined several possible statuses into one invalid filter on every case. The record lookup failed, so it often could not produce a useful answer. The baseline had 0/10 answer passes and 0/10 expected-path passes.

## What we changed and why

We measured the common failure first, then changed one prompt instruction: omit the optional status filter unless the question needs it; if needed, send one valid status. The model, ten claims, tools and budget stayed fixed. We added expected tool paths and checks so the final answer and the steps are scored separately. This tests whether the prompt fix addresses the observed problem without hiding regressions.

## Main files to show

Added for this work are marked **new**; existing files changed for the week are marked **updated**; reused files are marked **reuse**.

| File | Status and reason |
|---|---|
| `backend/app/agents/claims.py` | **Updated:** added the one prompt mitigation to the existing claims agent. |
| `course/claims_trajectories.py` | **New:** defines expected paths and scores answer and path separately. |
| `course/claims_race.py` | **New:** runs the fixed ten-case comparison. |
| `course/week8_questions.json` | **Reuse:** frozen fictional questions keep the comparison stable. |
| `tests/test_claims_trajectories.py` | **New:** checks path expectations and scoring. |
| `frontend/src/features/runs/Benchmarks.tsx` | **Added in the claims-workbench integration:** lets the mentor inspect metrics and saved traces. |
| `frontend/src/features/runs/MentorDemo.tsx`, `backend/app/services/mentor_demo.py` | **New:** typed live before/after demo, scoped to one claim. |
| `tests/test_mentor_demo.py` | **New:** checks the live demo request boundary. |
| `docs/demos/evidence/claims-race/` | **Evidence:** fixed results and traces; never overwrite. |

## Start the frontend and backend

Use two PowerShell terminals from the repository root. Ollama must be running with the configured model, normally `llama3.2:3b`.

**Terminal 1 — backend API**

```powershell
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Check `http://127.0.0.1:8000/docs` for the API. The backend calls the local model and returns the answer, tool steps and usage.

**Terminal 2 — React frontend**

```powershell
Set-Location frontend
$env:API_PROXY_TARGET = 'http://127.0.0.1:8000'
npm run dev -- --host 127.0.0.1 --port 5173
```

The browser page sends requests to the backend through Vite's `/api` proxy.

## Show the mentor

1. Open **Week 8 live demo**. Read the Before / Issue / Change / After story aloud.
2. Keep the example claim `CLM-2026-10004`. Click **Run before and after**.
3. Expand each tool trajectory. Point out the arguments, tool response, answer, time, tokens and estimated cost.
4. Click **Show saved C04 before and after** to compare with the original fixed experiment.
5. Open **Trajectories** and select `mitigation-r4`; show C04's answer and repeated clause lookup.
6. Optional: enable the injection-note test. Explain that it is a separate safety probe and not the Week 8 prompt fix.

The live API request is `POST /api/v1/claims/demo/run`, for example:

```json
{"task":"Summarize status for CLM-2026-10004","variant":"after","injection":false}
```

The response includes `run`, `diagnostics`, `variant` and `trace_id`. The saved case lets you show the same historical output without rerunning the model.

## Evidence and what it means

Saved baseline versus mitigation: answer passes **0/10 → 5/10**; invalid-argument cases **10 → 2**; full expected-path passes **0/10 → 0/10**. Repeated-call failures rose **0 → 8**. Median time increased about **27 seconds** and tokens increased **8,653**. Five cases had a passing answer but a failing path. C04 is a clear example.

Evidence: `baseline-r4/summary.json`, `mitigation-r4/comparison.json`, and `mitigation-r4/agent-C04.json` under `docs/demos/evidence/claims-race/`. These are deterministic checks on fictional data, not human labels or proof of general reliability. Cost is estimated. Current repository validation: 218 backend tests, five frontend unit tests, production build, and the Week 10 browser journey passed; see `docs/architecture/completion-report.md` for context.

## Simple talk track

“I’m checking two things: did the agent answer correctly, and did it use the right steps? Before Week 8 it sent an invalid status filter on all ten claims. We changed one instruction. Five answers now pass, but none of the agent runs pass the full path check, and repeated calls increased. So the fix helped one problem but did not make the agent fully reliable.”
