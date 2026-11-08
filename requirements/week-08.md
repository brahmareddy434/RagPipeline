# Week 08 — Claims trajectory evaluation and one mitigation

Status: draft v0.1; approval pending. Source: user requirements, 2026-11-05. Initial extraction; no approved prior specification changed.

## 1. Week and objective
Expose outcome-vs-trajectory gaps and measure one fix to the top failure mode.

## 2. Business requirements
Avoid relying on a correct answer reached through an unsafe or lucky path.

## 3. Functional requirements
10 claim cases with expected sequences and legitimate alternatives; tool-choice accuracy, real-argument validity, step efficiency, cost p50/max; gap and named right-answer/wrong-path example; exactly one mitigation; per-mode regressions and numeric price.

## 4. Non-functional requirements
Preserve prior behavior, reproducible evidence, safe failures and maintainable boundaries. High audit findings block real-data production release; no automated coverage decision or payout is authorized.

## 5. Technical requirements
Define acceptable paths before running; validate claim/clause IDs against the actual dataset rather than syntax alone. Freeze other variables across mitigation.

## 6. Backend requirements
Trajectory evaluator, visible evidence/run steps and guard boundaries; retain both baseline and after records with provenance.

## 7. Frontend requirements
Show outcome versus path separately, case-level tool traces, alternative accepted paths and regression counts.

## 8. Database requirements
Immutable cases, expected-path versions, run metrics and source revision; keep original evidence even when failures improve.

## 9. AI Agent requirements
Count loops/wrong tool/made-up arguments/giving up quietly. Choose one mitigation based on actual frequency and consequences, not aesthetics.

## 10. RAG requirements
Keep model, corpus and retrieval constant during the agent mitigation experiment; inspect whether policy exclusions were actually consulted.

## 11. API requirements
Reuse run outputs; add explicit fields only with backward-compatible contracts or a new version.

## 12. Security requirements
Use fictional/authorized injection cases; prompt-injection defenses and least-privilege checks must not claim complete protection.

## 13. Performance requirements
Report cost p50 AND max, outcome minus trajectory pass rate, mode delta, and numeric latency/token/cost/quality tradeoff.

## 14. Dependencies on previous weeks
Week 07 comparable claims agent and ten-case dataset; prior failure taxonomy.

## 15. Acceptance criteria
- **W08-AC01**: Ten cases define expected tool sequences and sets of legitimate alternatives before evaluation.
- **W08-AC02**: Report four trajectory metrics including argument reality checks and cost p50/max.
- **W08-AC03**: Report numeric outcome-minus-trajectory gap and one named outcome-pass/path-fail case with trace.
- **W08-AC04**: Apply exactly one mitigation to the measured top mode and show before/after count plus measured price.
- **W08-AC05**: Regression table lists checked modes, new/worsened modes or explicit absence with counts.

## 16. Test scenarios and traceability
Existing course/trajectory_eval.py and test_agent.py are HR foundations; add claims path alternatives/real-ID/metric boundary cases during implementation.

- W08-AC01 -> planned W08-V01: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.
- W08-AC02 -> planned W08-V02: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.
- W08-AC03 -> planned W08-V03: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.
- W08-AC04 -> planned W08-V04: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.
- W08-AC05 -> planned W08-V05: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.

Reusable source/evidence: course/trajectory_eval.py, course/week8_questions.json, docs/KT_Week8_Failure_Modes_and_Trajectory_Evals.md.

Current status: **Ten-claim baseline, one prompt mitigation, actual before/after traces and regression table complete.** The mitigation improved outcome/argument validity but introduced repeated calls and did not improve path pass rate. See [Week 08 demo](../docs/demos/week-08-demo.md).

## 17. Out-of-scope items
Multiple simultaneous mitigations; claims of robustness from one injection phrase; invented before/after scores.

## 18. Risks and assumptions
The supplied Week 8 text is truncated; the five explicit criteria above are retained. Existing HR numerical results are historical and cannot be relabelled as claims.

## Live mentor demo amendment - 2026-11-06

User requested typed questions with explicit before/issue/change/after explanations. Add `/demo/week8` and `POST /claims/demo/run` (also `/api/v1`): task, before/after variant, optional fixed fictional injection note. The only normal-arm difference is the existing `invalid_arguments` prompt instruction. Use identical fixed budgets and request-scoped tools. Do not overwrite the r4 artifacts or present fresh custom questions as the ten-case score. The injection test appends data to a notes observation, never the fixture; report whether the attack was actually delivered and require inspection rather than declaring marker absence a security pass. This extends presentation/verification for W08-AC03/04 without changing their historical scoring ruler. Backend contract/isolation and browser-flow checks: `tests/test_mentor_demo.py`, `frontend/e2e/mentor-demo.spec.ts`.

Amend approved scope using [change control](README.md).

## Execution amendment - 2026-11-06
User-authorized implementation adds predeclared expected paths, repository-backed argument checks, outcome/trajectory separation, cost p50/max, React case inspection and one prompt-only mitigation selected from the completed baseline's top failure mode. Baseline and mitigation runs preserve model, budgets, frozen source hashes and fixtures. No real-world labels or generalized robustness claims are made. See [Week 08 demo](../docs/demos/week-08-demo.md).

Baseline result: agent outcome/path pass 0/0 (gap 0), tool choice 1.00, argument validity 0.69, step efficiency 0.935, estimated cost p50 $0.001087 and max $0.001608. The fixed workflow was outcome/path pass 0.50/1.00 (gap -0.50), argument validity 1.00, step efficiency 1.00, estimated cost p50 $0.000524 and max $0.000757. The mitigation is one added instruction to omit an unrequested optional status filter, selected because invalid arguments were the measured agent failure mode in all 10 baseline cases. Invalid arguments fell 10 -> 2, but repeated calls rose 0 -> 8; the mode table shows zero baseline/mitigation counts for the other classifier modes. Outcome pass rate improved 0% -> 50%, but trajectory pass remained 0%. The tradeoff was p50 latency +27,081 ms, total tokens +8,653 and estimated mean cost +$0.000237/claim (p50 $0.001484, max $0.001695 after). Tool-choice accuracy fell 100% -> 95%, argument validity rose 69% -> 93%, and step efficiency fell 93.5% -> 79%. Actual outcome-pass/path-fail cases are C04, C06, C07, C09 and C10 in `mitigation-r4`; their traces are retained. These deterministic proxy outcomes are not human labels or proof of general reliability.

## Mentor handoff documentation amendment - 2026-11-08
Keep `docs/demos/week-08-demo.md` as the single Week 8 mentor guide. It must explain the pre-Week-8 behavior and observed issue, state what changed and why, name the main files and their purposes, include frontend and backend demo steps, point to saved evidence, and provide a short observer-friendly spoken explanation. Keep it near 70 lines and use recorded evidence only.
