# Week 04 — Debug retrieval with exactly one change

Status: draft v0.1; approval pending. Source: user requirements, 2026-11-05. Initial extraction; no approved prior specification changed.

## 1. Week and objective
Measure hit-rate@3 and latency on the same 12 claims questions and isolate a single retrieval improvement.

## 2. Business requirements
Prevent semantically similar clauses from displacing exact exclusion/form/endorsement matches.

## 3. Functional requirements
Use 12 real adjuster questions with known correct chunk IDs, at least four exact-token cases; freeze baseline; inspect every miss; label R/G/Not-In-Corpus with evidence; apply BM25+RRF(k=60) OR cross-encoder top-25 reranking; compare fixed/unfixed cases.

## 4. Non-functional requirements
Preserve prior behavior, reproducible evidence, safe failures and maintainable boundaries. High audit findings block real-data production release; no automated coverage decision or payout is authorized.

## 5. Technical requirements
RRF fuses ranks, not incompatible raw scores. For the experiment, freeze model, corpus/version, chunking and test set. Bonus MMR is a separate measured experiment after the single-change result.

## 6. Backend requirements
Reuse inspect and retrieval services with configurable strategy; persist per-question ranks, chunk IDs, inspection and timings.

## 7. Frontend requirements
Inspection view shows retrieved passages, exact IDs, scores, ranks and source edition; React migration must preserve these diagnostics.

## 8. Database requirements
Stable correct chunk IDs and form/endorsement/edition metadata; no schema change solely to improve a score.

## 9. AI Agent requirements
Do not swap the model to fix a retrieval-labelled miss.

## 10. RAG requirements
Baseline hit-rate@3 before mutation; same 12 after; latency p50 before/after; R/G/missing-corpus labels from actual context and output.

## 11. API requirements
Reuse /inspect and /evaluate; any chunk-ID metric additions require a reviewed compatible contract.

## 12. Security requirements
Use authorized real questions with claimant identifiers removed; do not leak policy documents in public results.

## 13. Performance requirements
Report both hit-rate@3 and p50 latency; warm/cold cache conditions and hardware documented consistently.

## 14. Dependencies on previous weeks
Week 03 index, known chunk IDs and a real adjuster question sample.

## 15. Acceptance criteria
- **W04-AC01**: golden_set.jsonl contains 12 authentic questions, correct chunk IDs and at least four exact-token questions with provenance.
- **W04-AC02**: Baseline is recorded before changing retrieval; every miss has an inspection-backed R/G/Not-In-Corpus label and tally.
- **W04-AC03**: Code/config diff changes exactly one retrieval variable: RRF(k=60) or top-25 cross-encoder reranking.
- **W04-AC04**: results.md reports same-set before/after hit-rate@3 and p50 latency, per-case fixed/unfixed status and justified shipping decision.
- **W04-AC05**: Optional MMR reports hit-rate and diversity separately and identifies any correct-edition displacement.

## 16. Test scenarios and traceability
Existing retrieval tests validate ranking primitives, not this rubric. Add experiment invariants for frozen inputs/config and inspect live saved ranks; planned Track D dataset is pending.

- W04-AC01 -> planned W04-V01: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.
- W04-AC02 -> planned W04-V02: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.
- W04-AC03 -> planned W04-V03: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.
- W04-AC04 -> planned W04-V04: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.
- W04-AC05 -> planned W04-V05: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.

Reusable source/evidence: app/retrieval.py (BM25/RRF/rerank options), /inspect and /evaluate, course/run.py. Existing evidence is largely HR.

Current status: **Fictional 12-question retrieval experiment delivered: semantic and RRF both 12/12; no accuracy gain claimed.** Authentic adjuster questions remain pending. See [cross-week traceability](../docs/architecture/traceability.md).

## 17. Out-of-scope items
Model changes, simultaneous hybrid+reranker changes, invented questions labelled real.

## 18. Risks and assumptions
User's Week 4 theory repeats Week 3; the distinct Week 4 Task D practical defines this scope. Real adjuster questions and edition-specific corpus are missing.

Amend approved scope using [change control](README.md).

## Execution amendment - 2026-11-05
Authorized runner and React inspection implemented. W04-AC02-04 fictional experiment: semantic 12/12 -> RRF 12/12, p50 3.275ms -> 3.63ms; no gain claimed. See docs/demos/week-04-demo.md and dated manifests. W04-AC01 remains pending authentic adjuster questions. W04-AC05 optional MMR not run. No approved criterion is relaxed by the fixture demonstration.
