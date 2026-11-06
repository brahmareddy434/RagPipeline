# Week 04 - one retrieval change

Objective: W04-AC02-04 tooling and fictional demonstration; W04-AC01 authentic adjuster provenance remains pending. Optional MMR is not run.

## Start and show
Start backend/React using Week 03 commands. Open `/#/inspect`, enter `What does EX-FLOOD-02 exclude?`, compare Semantic and BM25 + RRF. Expand each passage to see exact IDs, rank, scores and document version.

Run from root: `.\.venv\Scripts\python.exe -m course.claims_retrieval retrieval`.
Inspect dated `manifest.json`, `golden-600.json`, `baseline-600.json`, `after.json` and `comparison.json` in `docs/demos/evidence/claims-retrieval/20261105T150007039001Z`.

`course/claims_retrieval.py` builds a disposable index; `course/insurance/retrieval-questions.json` declares 12 fictional questions, four exact-token cases and known supporting quotes. Golden IDs are resolved and saved before querying. The existing retriever changes only `mode` from semantic to hybrid, using RRF constant 60. Model, corpus, questions, chunk size 600/overlap 80, k=3 and reranking stay fixed. Query embeddings are warmed for both arms; baseline is saved before the after run.

## Results and decision
Both arms: 12/12 hit@3; semantic p50 3.275ms, hybrid 3.63ms. Fixed cases: zero; regressed: zero. No misses existed to classify; saved retrieval evidence permits R/Not-In-Corpus classification. Generation failures need actual answer inspection and are not inferred from retrieval ranks. No additional retrieval change is justified by this ceiling-limited fixture. Collect authentic, harder edition-sensitive questions before a shipping decision.

No new database or agent behavior. Existing ranking tests and the Week 03 targeted regression passed; UI build and five frontend tests passed. Self-review verified one-variable comparison, exact IDs and fixture provenance. The test set is too small/easy to establish insurance retrieval quality.

Talk track: Measure baseline first, inspect exact passages, then alter one variable. An unchanged perfect score is an honest result, not evidence that a new technique improved accuracy.
