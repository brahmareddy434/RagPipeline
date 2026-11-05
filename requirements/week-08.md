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

Current status: **HR trajectory evidence exists; Task D ten-claim results pending.** See [cross-week traceability](../docs/architecture/traceability.md). A generic test-suite pass does not replace acceptance evidence.

## 17. Out-of-scope items
Multiple simultaneous mitigations; claims of robustness from one injection phrase; invented before/after scores.

## 18. Risks and assumptions
The supplied Week 8 text is truncated; the five explicit criteria above are retained. Existing HR numerical results are historical and cannot be relabelled as claims.

Amend approved scope using [change control](README.md).
