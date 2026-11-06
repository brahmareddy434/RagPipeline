# Week 05 — Read 20 real traces and rank failures

Status: draft v0.1; approval pending. Source: user requirements, 2026-11-05. Initial extraction; no approved prior specification changed.

## 1. Week and objective
Produce an honest taxonomy from a seeded random sample and a prediction committed before any fix.

## 2. Business requirements
Turn vague claims-quality complaints into ranked, traceable failure modes.

## 3. Functional requirements
Replay one seeded random trace from trace content alone; document missing fields. Select 20 seeded random traces. Human writes one observation each without fixes, then clusters into 4–7 modes with count, percent, severity and example ID. Predict one measurable fix with date and commit hash.

## 4. Non-functional requirements
Preserve prior behavior, reproducible evidence, safe failures and maintainable boundaries. High audit findings block real-data production release; no automated coverage decision or payout is authorized.

## 5. Technical requirements
Trace prompt/version, retrieved IDs/text/scores, model/parameters, raw output and usage. Capture self-contained sanitized replay inputs; maintain a frozen source revision during open coding.

## 6. Backend requirements
Redact before persistence; trace export, seeded sampling and replay helpers; keep human notes separate from assistant suggestions.

## 7. Frontend requirements
Authorized trace reader/replay and notes view when requested; never expose private traces through a public static mount.

## 8. Database requirements
Immutable redacted trace/run IDs, sampled IDs/seed and separately controlled pseudonym mapping if needed. Document irrecoverable redactions.

## 9. AI Agent requirements
Record decisions/tool inputs/observations/stop reasons; replay limitations must identify stateful external dependencies.

## 10. RAG requirements
Store retrieved evidence and scoring/version provenance so a miss can be inspected without the mutable live index.

## 11. API requirements
Authorized trace access/export only when implemented; existing raw log files are not a secure trace API.

## 12. Security requirements
Confirm claimant names and CLM numbers redacted before write, including nested/error/model fields; restricted retention and replay access.

## 13. Performance requirements
Sampling reproducible at >1000 traces; bounded export/read; report actual trace volume rather than asserting 1000 records exist.

## 14. Dependencies on previous weeks
Weeks 03–04 and enough authentic production-like authorized claims traces.

## 15. Acceptance criteria
- **W05-AC01**: Seeded trace replay shows original and replayed output plus missing/unreconstructable fields.
- **W05-AC02**: Documented random seed selects 20 trace IDs; human open-coding notes contain one observation each before categories or fixes.
- **W05-AC03**: Zero code changes occur during the frozen open-coding phase; revision/diff evidence proves it.
- **W05-AC04**: taxonomy.md has 4–7 legible modes with count and percentage of 20, severity and example trace ID.
- **W05-AC05**: Dated falsifiable one-mode prediction with exact delta is committed before the fix; include commit hash and three benchmark-limit sentences.
- **W05-AC06**: Optional 10 curated-demo traces are compared separately against the random sample.

## 16. Test scenarios and traceability
Reuse trace logger tests as baseline; add redaction/replay/sampling invariants when implementing. Human authorship, observation quality and order require review, not synthetic test labels.

- W05-AC01 -> planned W05-V01: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.
- W05-AC02 -> planned W05-V02: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.
- W05-AC03 -> planned W05-V03: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.
- W05-AC04 -> planned W05-V04: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.
- W05-AC05 -> planned W05-V05: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.
- W05-AC06 -> planned W05-V06: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.

Reusable source/evidence: app/trace_logger.py, evaluation/collect_week5_traces.py, course/review_notes.py, tests/test_trace_logger.py.

Current status: **Pre-write redaction, fictional trace replay, synthetic sampling and React trace view delivered/tested.** Authentic human trace analysis remains pending. See [cross-week traceability](../docs/architecture/traceability.md).

## 17. Out-of-scope items
Fixing failures during coding; fabricating real traces/human notes; category-first sampling.

## 18. Risks and assumptions
Current TraceLogger writes unredacted payloads. Existing saved traces are HR; the required random claims corpus and human notes are unavailable.

Amend approved scope using [change control](README.md).

## Execution amendment - 2026-11-05
Pre-write redaction, exact provider payload capture, tenant-private trace reader/React view and seeded sample/replay/freeze verification implemented. W05-AC01 has a replay runner; W05-AC02-05 remain dependent on a real sample and human observation/taxonomy/prediction sequence. No human notes were generated. Optional curated comparison is not run. See docs/demos/week-05-demo.md for commands and explicit privacy/replay limitations.
