# Week 06 — Validate the claim-summary judge

Status: draft v0.1; approval pending. Source: user requirements, 2026-11-05. Initial extraction; no approved prior specification changed.

## 1. Week and objective
Measure agreement with 25 blind human labels before trusting a single binary judge criterion.

## 2. Business requirements
Prevent unvalidated model scores from driving claims operations.

## 3. Functional requirements
25+ mode-tagged cases with at least two verbatim real failure regressions; one-command mode table; at least two deterministic criteria removed from judge prompt; 25 blind labels saved before judge; v1/v2 iteration using two own disagreements; prediction before iteration and honest assessment.

## 4. Non-functional requirements
Preserve prior behavior, reproducible evidence, safe failures and maintainable boundaries. High audit findings block real-data production release; no automated coverage decision or payout is authorized.

## 5. Technical requirements
Claim ID format, parseable date of loss, numeric deductible and denial-clause citation are assertion candidates. One remaining binary criterion; no vague 1–10 tolerance score.

## 6. Backend requirements
Separate assertions, judge interface, evidence runner and agreement calculation; store actual outputs and complete token/cost usage.

## 7. Frontend requirements
Evaluation table by failure mode and disagreement inspection; blind label UI must hide judge verdicts until sealed.

## 8. Database requirements
Immutable case revisions, labels_25.json, timestamp/commit receipt, prompt hashes and run ordering; no relabelling to inflate agreement.

## 9. AI Agent requirements
Do not let the answer-producing agent grade itself without independent human validation.

## 10. RAG requirements
Judge policy-backed summaries using the correct policy edition and evidence; optional RAGAS is separately labelled and measured.

## 11. API requirements
Evaluation workflows may stay CLI initially; add authorized versioned report/label routes only with frontend scope.

## 12. Security requirements
Redact summaries and notes; restrict labels/run access; keep provider credentials out of prompts/reports.

## 13. Performance requirements
Report assertion count versus judged-criterion count and per-mode pass rates; deterministic checks avoid unnecessary model calls.

## 14. Dependencies on previous weeks
Week 05 authentic taxonomy, frozen failed traces and completed blind human grading.

## 15. Acceptance criteria
- **W06-AC01**: One command evaluates 25+ mode-tagged claims cases including two verbatim real regression cases.
- **W06-AC02**: At least two named criteria are deterministic assertions and absent from both judge prompts; report counts.
- **W06-AC03**: 25 human blind labels have verifiable pre-judge ordering; no assistant-created labels passed off as human.
- **W06-AC04**: Agreement percentages before/after are computed from the same sealed labels; v2 includes two actual v1 disagreements.
- **W06-AC05**: prediction.txt predates iteration; analyze two disagreements with who was right and where prediction failed.
- **W06-AC06**: Optional RAGAS demonstration reports both faithfulness and context precision for a wrong-wording case, without averaging away the error.

## 16. Test scenarios and traceability
Existing test_week6_week7.py covers portions of HR agreement/sealing. Claims assertions, date/number edge cases, ordering/label-integrity and mode-table tests are planned.

- W06-AC01 -> planned W06-V01: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.
- W06-AC02 -> planned W06-V02: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.
- W06-AC03 -> planned W06-V03: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.
- W06-AC04 -> planned W06-V04: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.
- W06-AC05 -> planned W06-V05: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.
- W06-AC06 -> planned W06-V06: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.

Reusable source/evidence: evaluation/week6/*, app/week6_assertions.py, tests/test_week6_week7.py; domain is HR.

Current status: **Reusable evaluator pattern exists; Task D data, assertions and judge-validation evidence pending.** See [cross-week traceability](../docs/architecture/traceability.md). A generic test-suite pass does not replace acceptance evidence.

## 17. Out-of-scope items
Operational routing by an unvalidated judge; synthetic human labels; changing the scoring ruler to force a gain.

## 18. Risks and assumptions
HR sealed labels cannot validate claims summaries. Human grading and real claims regressions are required external inputs.

Amend approved scope using [change control](README.md).
