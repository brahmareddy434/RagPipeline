# Week 10 mentor demo — claims squad vs single agent

Week 10 tests whether a small manager-plus-two-specialists team improves fictional insurance-claim triage enough to justify its extra prompts. Open the React demo at `http://127.0.0.1:5173/#/demo/week10`. The UI labels the available ten-case run as provisional: the repository does not identify the required ten Week-6 Task D questions and completed judge.

## Start the local demo

Use a fresh local database for this run so it cannot write to the existing Chroma collection. In PowerShell, start the backend from the repository root:

```powershell
$env:CHROMA_PATH='data/week10-demo'
$env:COLLECTION_NAME='week10_demo_docs'
$env:MEMORY_COLLECTION_NAME='week10_demo_memory'
$env:TRACE_LOG_PATH='logs/week10-demo-traces.jsonl'
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In a second terminal:

```powershell
$env:API_PROXY_TARGET='http://127.0.0.1:8000'
Set-Location frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

Prerequisites: Python dependencies in `.venv`, frontend dependencies in `frontend/node_modules`, Ollama at the configured local URL, and the configured chat model pulled locally. The task uses fictional claims only. No A2A endpoint is implemented; the API exposes a proposed AgentCard description. Estimated cost uses the app's token reference rate, not an Ollama invoice.

## What changed

Before Week 10, one agent read the claim record, adjuster notes, and policy clauses, then generated a grounded summary. The Week 8 evaluator already measured outcome and tool-path behavior. Week 10 adds an orchestrator that asks a manager model to assign a coverage/exclusions review and a notes review, passes the specialists only their relevant read-only evidence, and validates their exact source quotations before deterministic synthesis. This addresses a specific observed risk: the local model's free-form final synthesis attached the missing-estimate fact to the wrong numeric claim context and abstained. The manager now checks the original sources and uses the existing grounding validator.

## Live steps

1. In the sidebar choose **Week 10 live demo**. Read the yellow cohort limitation before running the paired case.
2. Keep `CLM-2026-10001` and the example question. Select **Run single and team**. Both arms receive the exact same user query, fictional claim, server-owned budget and local model. Inspect each answer, tool steps, latency, token total, cost estimate and citations. This one-off query is not judge-scored; the paired ten-case race below applies the same Week 8 judge to both arms.
3. Compare with the sample's expected evidence: status `awaiting_documents`, the missing repair estimate note, and clause `DOCS-MOTOR-09`. The team must not decide coverage or payment.
4. Select **Inject coverage worker 500**. This is an in-process fault fixture, not a network request to a remote worker. Inspect that the run stops, records status 500, abstains from a coverage conclusion and does not retry.
5. The page loads the saved paired race automatically. The recorded run used `llama3.2:3b` on C01–C10: single/team outcome pass proxy 0%/90%, p50 48.2s/18.9s, p99 70.1s/31.1s, tokens 54,284/6,780, estimated cost per claim $0.001239/$0.000207, and token multiplier 0.1x. The largest team hand-off was `manager->coverage_worker` at 53.2% of team tokens. Open its table, per-handoff log, failure evidence and verdict. To collect a fresh run, choose **Run a new ten-case race**; it alternates arm order, applies unchanged `course.claims_trajectories.assess` to both arms, and writes a new timestamped evidence directory.
6. Open **Proposed AgentCard**. Point out its advertised skill, JSON input/output modes and auth scheme. The failed run maps to A2A `failed`; `input-required` applies only when a human adjuster must supply information. A2A standardizes agent discovery and task lifecycle semantics; a plain REST call can invoke a worker but has no such shared agent-task contract by itself.

Equivalent API request (same query is used for both arms):

```json
{"claim_id":"CLM-2026-10001","arm":"both","task":"Summarize status and unresolved issues for CLM-2026-10001, including any exclusion review needed. Cite the relevant policy clauses. Do not decide coverage."}
```

Expected response fields include `single`, `team`, each arm's `answer`, `steps`, citations and `usage`, plus `task_state`. On the example, look for the unresolved repair estimate and `DOCS-MOTOR-09`; never expect an approval or payment decision. The `failure` arm injects one known 500 and must return `task_state: "failed"` with `stop_reason: "worker_error"`.

## Files and contracts

- `backend/app/agents/claims_team.py` owns typed planning, the narrow specialists, shared deadline/provider budget and verified-quote synthesis.
- `backend/app/infrastructure/budgets.py` reserves prompt and output budgets before concurrent provider calls; `backend/app/infrastructure/ollama.py` records measured or upper-bound usage with hand-off ownership.
- `course/claims_team_race.py` freezes the provisional fixture, runs both arms, calls the same deterministic judge, calculates p50/p99 and writes the artifacts.
- `backend/app/controllers/claims.py` exposes the paired run, fault fixture and proposed AgentCard.
- `frontend/src/features/runs/Week10Demo.tsx` presents the before/issue/change/after narrative and live evidence.
- `requirements/week-10.md` records acceptance IDs and the outstanding Week-6 cohort dependency.

## Evidence and limits

The saved race includes all ten case IDs, fixture and judge hashes, model, budget, p50/p99 latency, total measured tokens, mean reference cost per claim, hand-off prompt/completion tokens, multiplier, largest hand-off share, injected 500 behavior, and a verdict of at most ten lines naming sunk-cost bias. Evidence is in `docs/demos/evidence/claims-team-race/provisional-week7-8-20261108T095600-468812Z/`. It is assistant-run evidence over fictional Week-7/8 cases, not a submission-complete Week-6 comparison. W10-AC01 remains pending until the specified case set and judge are identified.

## Talk track

“The team did not get a free win just because it has more agents. Both arms saw the same claim and judge. We measured answer quality, p50 and p99 latency, tokens and estimated cost, then injected one exclusions-worker failure. The manager stopped safely. These are local fictional results; the exact Week-6 claims cohort is still missing, so this provisional comparison does not claim that rubric item is complete.”
