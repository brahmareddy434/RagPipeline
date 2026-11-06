# Execution report - 2026-11-05

# Execution report - 2026-11-06

User authorization covers Weeks 01-09, the backend restructuring and React frontend. This report records local implementation and verification, not human or real-world acceptance. The prior [Codex handoff](../CODEX_HANDOFF.md) is an archived snapshot superseded by this report and the current [traceability matrix](traceability.md). Claims fixtures are fictional; human annotations, real provider access and peer attestations remain external acceptance inputs.

## Week 02 checkpoint

Fresh baseline: 176 backend tests passed (32.82s, three deprecation warnings), four frontend tests passed and React production build passed. The first sandbox run could not create MCP subprocess pipes; the permitted rerun exercised the real fixture servers. Vite also required process permission. Ollama tags confirmed llama3.2:3b and nomic-embed-text:latest installed.

Separate self-review examined access/roles, tenant collection and source isolation, client cancellation, static routes, schema validation and lifecycle cleanup. Corrected model argument validation to avoid reflecting invalid values in HTTP errors. No introduced Critical/High findings remain in this increment. Pre-existing trace redaction and agent budget findings remain release blockers until later increments. Token access is a single-worker local training boundary, not enterprise OIDC.

Browser integration and later-week validation will be recorded below as executed. No independent reviewer was used.

## Weeks 03-04 checkpoint
26 targeted backend tests passed; five frontend tests and production build passed. Two real headless Edge journeys passed in 20.0s against an isolated Uvicorn/Chroma instance and live Ollama: upload/ask/source/delete and structured calculator. Port 8765 was occupied; tests use 18765 without stopping the existing service. Live chunking and retrieval outputs are linked in the weekly demos. The retrieval fixture reaches 12/12 in both arms; no accuracy gain claimed. Review is self-review. Authentic policy and adjuster provenance remain pending.

## Week 05 checkpoint
27 targeted backend tests passed, including pre-write redaction and seeded 1,100-record synthetic sampling; five frontend tests/build passed. Separate self-review checked raw/error/nested fields, export isolation, replay side effects and source freeze checks. No human coding/labels were authored. Redaction covers the documented fields/patterns/configured names; arbitrary unlabelled personal names and production retention remain release limitations. Raw MCP wire recording remains explicitly restricted to fictional protocol experiments because altering its bytes would invalidate that evidence.

## Week 06 checkpoint
11 evaluation/trace tests passed; five frontend tests and production build passed. Thirty synthetic cases run in one command: five valid and five semantic-overclaim cases pass mechanical assertions; all 20 cases with invalid IDs/dates/deductibles/clauses fail the intended check. Four deterministic criteria and one pending semantic criterion are explicit. Self-review corrected the v2 examples to exclude deterministic fields. Real regressions, human labels and prediction are pending; no model judge run or agreement score is claimed.

## Weeks 07-09 and React checkpoint

Week 07's complete ten-case `llama3.2:3b` baseline is in [baseline-r4](../demos/evidence/claims-race/baseline-r4/). The fixed workflow scored 50% on deterministic outcome checks and 100% on expected paths; the agent scored 0% on both, with invalid arguments in all ten cases. The fixed workflow was faster (33.3s vs 47.7s p50) and used fewer tokens (19,054 vs 54,264). Reference cost estimates and all comparison metrics are in the summaries and Week 07 requirements. The 500-token admission boundary produced a clean zero-call abstention.

Week 08's single status-filter prompt mitigation preserved the baseline model, budget, fixtures and frozen source hashes. Invalid-argument failures fell 10 -> 2 and outcome passes rose 0% -> 50%, while repeated-call failures appeared 0 -> 8 and trajectory pass stayed 0%. It cost +27.1 seconds p50, +8,653 total tokens and +$0.000237 estimated mean cost per claim. Five outcome-pass/path-fail traces are present. These are deterministic proxies over fictional cases; no human label or general reliability claim is made.

Claims agent/workflow, trajectory and MCP inventory/trace pages are implemented in the React app. Final verification: backend suite **199 passed** (3 dependency deprecation warnings); React unit suite **5 passed**; TypeScript check and production build passed; **5/5 Edge journeys passed**, including three mocked claims-page tests and live Ollama document/Q&A/source/delete and calculator flows; **6/6 Postman requests and assertions passed** against the local API, including discovered MCP tools and the versioned benchmark report. The Postman CLI did not publish a cloud run because this machine is not logged in; local assertions all executed.

The five local code-review skills were followed in one self-review pass; no separate reviewer was involved. The final self-review found no introduced Critical/High issue for this fictional local training scope. Real claimant deployment is still blocked on identity, tenant authorization, real-document provenance, human review, peer evidence and operational controls. Optional W07 long-note/cross-process memory was not run. W08's outcome-pass/path-fail examples are from the measured fictional model run, not fabricated human judgments.

Cleanup removed generated frontend test output and verified Python cache directories outside `.venv`. The production frontend build is retained because the local API serves it directly. `.env`, `.venv`, databases/data (including isolated browser-test databases), uploads, logs, recovery backups and every partial/historical/completed experiment artifact are preserved. The old handoff is an explicit superseded archive pointer; the current README, traceability matrix and execution report are authoritative.
