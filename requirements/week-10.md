# Week 10 — Multi-agent and A2A, with evidence

Status: requested and authorized by the user on 2026-11-08. Domain: Task D, fictional insurance claims. This spec preserves the supplied Task Set D and records a missing-input deviation before implementation. The implementation and local mentor demonstration may proceed; no result may be represented as satisfying the exact Week-6 comparison until the specified cohort is established.

## 1. Week and objective
Test whether a manager plus two narrow claims specialists improves the existing claims agent on the same ten questions under the same judge, after including latency, tokens, estimated cost, repeated context, and worker failure.

## 2. Business requirements
Enable the claims lead and mentor to decide from observed evidence whether the team should be kept. Preserve uncertainty; do not provide coverage decisions or payment authorization.

## 3. Functional requirements
Manager plans two independent assignments: coverage/exclusion review and adjuster-note summary. Specialists receive only the query and relevant evidence. Manager synthesizes their typed results. Race against the existing single claims agent. Record answer quality, p50/p99 latency, total tokens, cost per claim, each hand-off's actual token usage, multiplier and largest share. Inject one coverage worker HTTP 500 and report the observed recovery behavior. Produce `race_table.md`, `handoffs.log`, `failure_case.md`, and a verdict of at most ten lines naming sunk-cost bias.

## 4. Non-functional requirements
Fictional, bounded, reproducible and side-effect free. No model framework or library without demonstrated need. One frozen case revision, model, budget and judge per paired run. Do not replace or mutate Weeks 6–9 evidence.

## 5. Technical requirements
Use the existing Ollama provider, token accounting, `AgentBudget`, fictional claims repository, accepted clause paths and quality evaluator. Keep manager and specialist roles typed and narrow. Run specialists concurrently where safe; include actual provider counts, not estimates, in token totals. Reference-rate dollar costs must be labelled estimates, not an Ollama invoice.

## 6. Backend requirements
Add a team orchestration service and run boundary. Preserve `claims_agent` as the single-agent arm. Keep separate specialist failures observable; do not turn an exclusion-worker failure into a coverage assertion. A failed, required coverage check must cause a safe partial answer or abstention and be recorded.

## 7. Frontend requirements
Add a Week 10 mentor page. Show the prior single-agent behavior, identified reason for the team, what changed, and the actual after result. Allow typing one query, running both arms and opening hand-off logs, case metrics, failure evidence, verdict and the advertised AgentCard. Show loading/error/empty/success states and clear that runs use fictional data.

## 8. Database requirements
No schema migration. Preserve the existing fixture. Write each new evaluation attempt to a fresh, explicitly named output directory; never overwrite frozen evidence.

## 9. AI Agent requirements
Use an orchestrator-worker pattern with a manager and two specialists: (1) coverage/exclusions, (2) adjuster notes. Specialists do not share tools beyond their assigned read-only evidence. Manager retains final responsibility, exposes missing-worker state, and cannot claim coverage approval. Compare with the same single agent on each case.

## 10. RAG requirements
Reuse the exact policy clause text and claim notes returned by existing claims tools. Verify all cited IDs against gathered evidence. Treat user query, model output, claim notes, policy text and MCP output as untrusted data.

## 11. API requirements
Expose bounded, version-compatible team-run and report operations. Validate one known fictional claim per live query. Failure injection is an explicit test-only request option limited to a selected known case; it cannot select commands, endpoints or arbitrary worker behavior. Provide an AgentCard representation with skills, input/output modes and declared auth.

## 12. Security requirements
No real claimant records, tokens or model credentials in fixtures or reports. Do not enable untrusted worker endpoints or public arbitrary fault injection. Apply request budgets and timeout to manager, both specialists and synthesis; record any incomplete provider usage. The demo is a loopback fictional-training capability and makes no production-security claim.

## 13. Performance requirements
For both arms report pass rate, p50 and p99 case latency, total model tokens, and mean estimated cost per claim. Report `team tokens / single tokens` to one decimal place, and identify the measured highest-token named hand-off and its share. Include model, budget, fixture/evaluator hashes and run timestamp. Keep failed-call reserved usage in totals with the recorded upper-bound status.

## 14. Dependencies on previous weeks
Week 7/8 ten-claim fiction, expected paths and `course.claims_trajectories.assess`; Week 9 MCP evidence and host/server concepts. Existing Week 6 contains 30 synthetic claims assertion cases and pending human judge labels, not a named ten-case claims judge cohort. The existing `evaluation/week6/eval_set.json` is HR Task Set C. These are not relabelled as the requested Week-6 claims cases.

## 15. Acceptance criteria
- **W10-AC01**: The same ten Week-6 Task D cases and unchanged Week-6 judge run through both arms. Record case IDs, fixture/judge hashes, and provenance. **BLOCKED on source input**: no named ten-case Week-6 claims set or completed claims judge is present. A local provisional race may reuse the established ten Week-7/8 claims with `assess`, but it must be labelled as a substitute and does not pass this criterion.
- **W10-AC02**: `race_table.md` reports outcome pass rate, p50/p99 latency, total tokens and estimated cost/task for both arms on the paired ten cases, with metric definitions, provenance and model.
- **W10-AC03**: `handoffs.log` records every manager/worker/synthesis transfer and actual prompt, completion and total provider tokens per case.
- **W10-AC04**: Compute team/single total-token multiplier to one decimal and name the largest measured hand-off plus its share of all team tokens.
- **W10-AC05**: Inject exactly one coverage/exclusions worker 500 response on one case. Retain response and trace; state whether manager retried, safely degraded/abstained, or issued an unsupported coverage claim.
- **W10-AC06**: `verdict.md` is at most ten lines, says sunk-cost bias by name, keeps or kills the team, and cites at least two reported metrics.
- **W10-AC07**: Report records are inspectable from the React demo and contain one paired same-query live run.
- **W10-AC08 (bonus)**: Advertise an AgentCard with skills, input/output modes and auth; map injected failure to A2A task state; explain A2A versus direct REST in two lines. Do not claim an A2A SDK or interoperable service if only the card and lifecycle mapping are implemented.

## 16. Test scenarios and traceability
Add provider-usage attribution and hand-off completeness tests; paired-input and same-judge tests; specialist isolation tests; failure-500 safe-degradation test; multiplier/p99 boundary tests; overwrite refusal; API validation/budget tests; UI before/issue/change/after and artifact inspection tests. Run targeted and full backend/React checks, browser journey, Postman local API assertions and real model race when Ollama is available. Keep mocked verification distinct from live evidence.

| Criterion | Verification target |
|---|---|
| W10-AC01 | Dataset audit, cohort hash check and runner guard; exact Task D cohort pending |
| W10-AC02–06 | Race summary and report validator over the exact paired outputs |
| W10-AC07 | Edge journey enters query, inspects both arms and all four artifacts |
| W10-AC08 | AgentCard schema/API assertions and injected-failure lifecycle evidence |

## 17. Out-of-scope items
Production claims decisions, real claimant records, agent-team frameworks, a deployed A2A service, invented Week-6 human labels, and describing Week-7/8 cases as Week-6.

## 18. Risks and assumptions
The supplied prompt explicitly says “same 10 Week-6 eval cases” and “same judge.” The repository cannot substantiate such a cohort. A substitute experiment is useful for a mentor demo but does not meet W10-AC01 or the full 100-point submission until the mentor/user supplies or identifies the cohort and judge. Local model results vary. Manager synthesis could omit an exclusion; the failure path must fail safely and the grader must score the same way for both arms.

## Change history
- 2026-11-08: initial extraction from the supplied Week 10 module brief and Task Set D. Exact Week-6 cohort is pending audit; no case or human label has been fabricated.
- 2026-11-08: added the provisional paired runner, typed local team API/UI, shared provider-budget reservations, proposed AgentCard, and injected in-process 500 behavior. W10-AC01 remains blocked; live paired metrics and artifact run are pending execution.
- 2026-11-08: completed the live provisional C01–C10 local-model race, injected-failure evidence, artifact API/UI loading and verification. W10-AC02–06 are evidenced only on this clearly labelled substitute cohort; W10-AC01 remains blocked pending the exact Week-6 Task D cases and judge.
