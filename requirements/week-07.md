# Week 07 — Race the claims agent against a fixed workflow

Status: draft v0.1; approval pending. Source: user requirements, 2026-11-05. Initial extraction; no approved prior specification changed.

## 1. Week and objective
Compare identical claims tasks with a bounded agent and fixed workflow using measured reliability, latency, tokens and cost.

## 2. Business requirements
Choose orchestration by whether the input changes the path, not by preference for agents.

## 3. Functional requirements
Third tool with one job and claim-status enum; same tools/model/output in both systems; 10 claims with at least three dependent cases; pass rate/p50 latency/total tokens/cost per claim; clean budget termination; verdict under 150 words.

## 4. Non-functional requirements
Preserve prior behavior, reproducible evidence, safe failures and maintainable boundaries. High audit findings block real-data production release; no automated coverage decision or payout is authorized.

## 5. Technical requirements
ReAct loop remains hand-built; fixed workflow contains no hidden decision loop. Describe memory/framework alternatives without installing them by default.

## 6. Backend requirements
Shared claims tools and output contract; strict max iterations/tokens/cost/deadline, covering tool calls, compression and finalization; full usage accounting.

## 7. Frontend requirements
Side-by-side workflow/agent runs, visible steps and stop reasons; compare claims using the same request context.

## 8. Database requirements
Fictional fixtures for tests and authorized cases for evaluation; scoped run memory. Bonus persists a policy excess across process restart.

## 9. AI Agent requirements
Tool descriptions non-overlapping; validate real IDs/enums; record decision/action/observation and all calls. Safe final response when budgets terminate.

## 10. RAG requirements
Policy exclusions supplied with correct provenance; triggered exclusions must be checked when notes reveal a relevant cause.

## 11. API requirements
Existing HR /agent/run, /workflow/run and /agent/race are compatibility baselines; claims domain needs a deliberate contract/config choice.

## 12. Security requirements
Read-only triage initially; deterministic payable computation is not payout authorization; isolate memory and notes, sanitize tool outputs.

## 13. Performance requirements
Four numbers for both systems on same 10 inputs; all per-lap provider calls counted; sequential race avoids shared local runner contention.

## 14. Dependencies on previous weeks
Validated claims retrieval, assertions and case mix from Weeks 03–06.

## 15. Acceptance criteria
- **W07-AC01**: Third tool has exactly one purpose, typed arguments and a claim-status enum; show description diff.
- **W07-AC02**: Fixed workflow uses identical inputs/tools/model/output contract and no agent loop.
- **W07-AC03**: Race uses the same 10 claims, at least three dependent cases, and produces all eight comparative metrics.
- **W07-AC04**: All four budgets are enforced; retain a real clean budget-termination log and full usage.
- **W07-AC05**: Verdict under 150 words names the input class requiring variable planning or admits none does.
- **W07-AC06**: Optional long-note experiment measures three cases and documents a lost detail plus cross-restart memory.

## 16. Test scenarios and traceability
Reuse test_agent.py and workflow-related checks; planned claims contract parity, enum/invalid-ID, strict timeout/finalization and usage-accounting tests.

- W07-AC01 -> planned W07-V01: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.
- W07-AC02 -> planned W07-V02: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.
- W07-AC03 -> planned W07-V03: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.
- W07-AC04 -> planned W07-V04: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.
- W07-AC05 -> planned W07-V05: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.
- W07-AC06 -> planned W07-V06: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.

Reusable source/evidence: app/agent.py, agent_tools.py, workflow.py, memory.py, course/race.py, tests/test_agent.py.

Current status: **Core orchestration exists; comparable ten-claim race and strict production budgets pending.** See [cross-week traceability](../docs/architecture/traceability.md). A generic test-suite pass does not replace acceptance evidence.

## 17. Out-of-scope items
Claims payment execution, hidden workflow agent, unsupported production memory guarantees.

## 18. Risks and assumptions
Current workflow/case mix is HR; budget checks have audit gaps. Fictional Week 9 claims fixtures contain only two claims, not the required ten.

Amend approved scope using [change control](README.md).
