# Week 10 Claims Squad Implementation Plan

> **For agentic workers:** Follow this plan inline in order. Each task uses test-first steps and records actual results. The active worktree is the user's `week-10` branch.

**Goal:** Compare a manager with two claims specialists against the existing single agent on ten identical fictional cases and let the mentor inspect live results and the honest report.

**Architecture:** Add a typed application service that invokes a planner, independently scoped exclusion and note specialists, and a grounded synthesizer. Keep `claims_agent` as baseline, `assess` as the common unchanged judge, and `expectations` as the provisional case source. Add a per-attempt CLI/artifact format and typed API/UI view. Fault injection is explicit, case-bound and cannot select executable services.

**Tech Stack:** Existing FastAPI/Pydantic, asyncio, HTTPX, Ollama, React/Vite, pytest/Playwright, installed Postman CLI. No new library.

**Spec:** `requirements/week-10.md`

## Global Constraints

- Use only the repository's ten assistant-authored fictional insurance claims.
- Label this as a provisional Week-7/8 fixture because the exact Week-6 Task D ten-case cohort is not identified.
- Pair both arms by identical question, case snapshot, model, judge, budget and runner revision.
- Preserve all existing evidence; write to a fresh output directory.
- Tool outputs and worker messages are untrusted. Never decide coverage or payment.
- Count actual model provider usage, including failed/cancelled reserved bounds.
- Keep the two specialists to read-only, purpose-limited capabilities and bound their work.
- Do not claim the typed AgentCard makes this service A2A interoperable.

## Review Focus

- Duplicate/missing claim IDs or corrupted fixture revision: reject before either arm runs.
- Invalid specialist arguments, unsupported clauses or misleading worker claims: validate against the fixture and gathered evidence; abstain when unsafe.
- Concurrent requests exhausting shared budgets or losing token ownership: reserve budgets before await and attribute each provider call to a named hand-off.
- Injected 500 during mandatory exclusion review: record failure; never return covered/approved.
- Existing output path or interrupted run: reject overwrite and preserve partial evidence.

---

### Task 1: Freeze the paired provisional case cohort and common judge

**Files:** Create `tests/test_claims_team_race.py`, `course/claims_team_race.py`.

**Interfaces:** `load_cohort(repository) -> list[dict]` returns exactly ten ordered IDs, each paired with `task_for(claim_id)` and predeclared accepted paths. `score_paired(single, team, cases, registry) -> dict` calls unchanged `assess` on both arms and asserts identical case order, task and hash.

- [ ] Write tests that 9/11/duplicate/mutated cohorts reject, all ten IDs preserve fixture order, and both arms invoke the identical judge against identical query strings.
- [ ] Run targeted tests; expect RED because the module is absent.
- [ ] Implement cohort loader and paired judge with fixture/evaluator hashes and `exact_week6_cohort: false` metadata.
- [ ] Run targeted tests; expect GREEN.

### Task 2: Attribute provider usage and apply a whole-run budget across workers

**Files:** Modify `backend/app/infrastructure/budgets.py`, `backend/app/infrastructure/ollama.py`; create `tests/test_provider_budget_reservations.py`.

**Interfaces:** Extend `ProviderBudget.admit()` to reserve estimated prompt and maximum output before an await; `settle(reservation_id, measured_prompt, measured_output)` on success and the reserved upper bound on error/cancel. Add a `provider_call_group` ContextVar copied into each usage metric.

- [ ] Write concurrent reservation and named ownership tests; run and verify RED.
- [ ] Implement in-event-loop reservations, settlement on every provider outcome, and call-group metrics.
- [ ] Test failure, cancellation, absent usage and parallel requests; ensure actual measurements replace reservations once.
- [ ] Run existing budget/provider tests.

### Task 3: Implement the manager, narrow specialists and honest 500 behavior

**Files:** Create `backend/app/agents/claims_team.py`, `tests/test_claims_team.py`; modify `backend/app/bootstrap.py`.

**Interfaces:** `ClaimsTeam(provider, repository).run(task, budget, fail_case_id=None) -> AgentRunResponse`. Strict models: `CoverageAssignment`, `NotesAssignment`, `SpecialistSummary`. The manager plan returns only the two permitted assignments. Specialists receive only the question and scoped record/notes/required-clause evidence. A matched injected fault raises typed `WorkerFailure(status_code=500)` before the coverage specialist model call; manager records 500 and abstains/returns a partial summary with no coverage conclusion.

- [ ] Write tests for specialist evidence scope, manager synthesis, shared evaluation trace, usage attribution, prompt-injection input and one 500 failure; run and verify RED.
- [ ] Implement typed planning, the two scoped workers and grounded synthesis with one shared absolute timeout and provider budget.
- [ ] Verify worker failure cannot yield a covered/approved assertion.
- [ ] Run existing claims-agent and provider-budget regressions.

### Task 4: Produce immutable race artifacts and mentor routes

**Files:** Modify `course/claims_team_race.py`, `backend/app/controllers/claims.py`, `backend/app/bootstrap.py`; create `course/claims_team_report.py`, `tests/test_claims_team_api.py`, `tests/test_claims_team_report.py`.

**Interfaces:** `POST /api/v1/claims/team/race` accepts one known fictional claim; budgets are server-owned. `POST /api/v1/claims/team/failure-demo` runs a case-bound 500. `GET /api/v1/claims/team/agent-card` returns a static local AgentCard description and says A2A transport is not implemented. CLI writes `race_table.md`, `handoffs.log`, `failure_case.md`, `verdict.md` (at most 10 lines), and compact `run.json` to a new directory only. p50 is median; p99 is nearest-rank. Cost is a reference estimate from actual/reserved tokens. Multiplier is one decimal `team total / single total`; top hand-off share denominator is all team tokens.

- [ ] Write report tests for hand-off completeness/ownership, multiplier, share, p99, verdict line limit, and overwrite refusal; API tests for invalid ID, arbitrary fault target and budget override. Run and verify RED.
- [ ] Implement fixed-budget API boundary and report writer.
- [ ] Run CLI with a test provider; validate report shape without overwriting.

### Task 5: Build the Week 10 mentor UI and API contract checks

**Files:** Create `frontend/src/features/runs/Week10Demo.tsx`, `frontend/e2e/week10-demo.spec.ts`; modify `frontend/src/app/App.tsx`, `docs/postman/Mentor_Demos.postman_collection.json`.

**Interfaces:** `/demo/week10` explains prior single-agent behavior, measured issue, team change and observed outcome; accepts one typed question, runs both arms and failure case, and displays handoffs/artifacts/AgentCard. Disclose that the exact Week-6 cohort is pending.

- [ ] Write browser tests for same query, results, failure, artifacts, AgentCard and validation/cancellation; verify RED.
- [ ] Implement typed API calls and accessible states.
- [ ] Run relevant React, browser and local Postman contract checks.

### Task 6: Run the live provisional race, document and review

**Files:** Create `docs/demos/week-10-demo.md`; update Week-10 requirements/index, traceability and completion report; create reviewed fictional evidence under a fresh `docs/demos/evidence/claims-team-race/<run>/` directory.

- [ ] Run full backend suite, frontend unit/build, relevant browser journey and local Postman API assertions.
- [ ] Run ten paired live cases and the separate 500 case if local Ollama is available. Record model, configuration, observed time/cost and limitations.
- [ ] Review spec fidelity, high risks, frozen evidence and provenance in a separate pass; disclose self-review when no fresh reviewer is available.
- [ ] Leave W10-AC01 pending until the exact Week-6 claims set and judge are identified.
- [ ] Commit a scoped Conventional Commit; do not push.

