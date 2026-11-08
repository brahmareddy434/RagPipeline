# Execution report - 2026-11-05

# Execution report - 2026-11-06

## Week 8/9 live mentor screens - 2026-11-06

Delivered `/demo/week8` and `/demo/week9`, linked from the sidebar and existing benchmark/MCP pages. Both explain prior behavior, the identified issue, the week's change and the resulting behavior. Typed questions run through both configurations with answer, tool trace and usage display. Week 8 also loads frozen C04 evidence and offers a separate request-local injection-note test. No fixture, existing benchmark or sealed submission artifact changed. No new dependency or database migration.

Validation: **204 backend tests passed** (three existing dependency deprecation warnings), **5 React unit tests passed**, TypeScript/production build passed, **7 distinct Edge browser scenarios passed** (three existing and four new; API replies mocked for those UI checks). Cancellation prevents dispatch of the second arm and switching weeks resets the question. The initial sandbox backend run failed eight MCP pipe tests; the permitted rerun exercised the real subprocesses successfully. Postman CLI 1.74.0 executed **5/5 local requests and assertions** against the real API, including actual two-tool/four-tool MCP discovery and invalid-input rejection. `postman status` is unsupported by this installed CLI; no cloud publication was performed.

Five additional real HTTP runs used live local Ollama, captured by `course/mentor_demo_smoke.py` in the local ignored directory `logs/mentor-demo-live-20261106/`. These are individual demo checks, not a rerun of the graded ten-case benchmark:

| Run | Observed answer/behavior | Tokens | Model-run time |
|---|---|---:|---:|
| Week 8 C04 before | Abstained; two tool errors and one repeat. | 7,068 | 125.1 s |
| Week 8 C04 after | Under review; pre-existing damage/exclusion review; zero tool errors, one repeat remains. | 6,498 | 94.9 s |
| Week 9 before | Policy-only tool call; abstained on claim status. | 3,086 | 51.7 s |
| Week 9 after | Discovered claims status call; answer says awaiting repair estimate, not coverage approval. | 4,787 | 56.6 s |
| Week 8 after with injected note | Attack delivered through notes; stopped on a repeated call, final answer abstained and did not contain the attack marker. This single case does not prove injection robustness. | 6,880 | 116.3 s |

Separate self-review (not an external reviewer) examined profile allowlisting, fixed budgets, claim scoping, fixture immutability, trace redaction, unchanged historical evidence, API compatibility, cancellation and honest result presentation. No introduced Critical/High finding for the fictional local demo scope. Existing production restrictions remain. Cancel stops browser waiting and prevents the next arm; already submitted server work can continue until its deadline. MCP discovery/setup occurs before the host's model-run deadline. Reviewed as approved for this local training scope.

The running project API on port 8000 was refreshed to load the new routes; the existing Vite server on 5173 remains available.

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

## Week 10 checkpoint — 2026-11-08

Implemented and live-tested the manager plus coverage/exclusions and adjuster-notes specialists, provider budget reservations and hand-off attribution, same-query API, proposed AgentCard, failure fixture, React mentor page, and timestamped race artifacts. The demo loads the saved race on entry. The local Ollama race used `llama3.2:3b` and the unchanged Week-8 assessor on C01–C10 from the existing fictional Week-7/8 fixture. Single/team outcome proxy pass rate was 0%/90%, p50 48.2s/18.9s, p99 70.1s/31.1s, total tokens 54,284/6,780, and estimated mean cost per claim $0.001239/$0.000207. Team/single token multiplier was 0.1x; `manager->coverage_worker` accounted for 53.2% of team tokens. One injected in-process coverage-worker 500 resulted in a safe abstention without retry or a coverage claim. This is actual local-model evidence and reference-rate cost, not an invoice.

Validation: **217 backend tests passed** (3 dependency warnings; full run with Windows named-pipe permission), **5 React unit tests passed**, TypeScript/production build passed, and the Week 10 Edge journey passed (1/1), including saved artifact load, same-query paired run, failure fixture and fresh-race artifact display. Postman collection JSON parses; Postman CLI was unavailable for local execution because the installed CLI reports a private-cloud manifest registry policy error. Direct API smoke checks returned API health, the saved race and AgentCard. Self-review only (no independent reviewer) found no introduced Critical/High finding for the fictional local-demo scope; production controls remain outside this task.

W10-AC01 remains blocked: the exact ten Week-6 Task D claim questions and their completed judge are not identified in this repository. The provisional evidence does not satisfy that requirement. The user can inspect the saved provisional result at `http://127.0.0.1:5173/#/demo/week10`; the isolated API uses loopback port 18767 and isolated Chroma data. No push or merge was performed.
