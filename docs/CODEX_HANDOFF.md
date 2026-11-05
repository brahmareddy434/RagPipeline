# Codex handoff - resume the authorized Weeks 01-09 implementation

Prepared 2026-11-05 after the user requested a status/handoff because their session limit was approaching. This document records the actual working tree and executed checks. Resume from here; do not restart the project or discard the uncommitted Week 02 work.

## Completion count

**One of nine weeks has completed, committed agent-deliverable work: Week 01.** Its learner-authored explanation and mentor sign-off remain human acceptance tasks. Week 02 has substantial implementation and passing tests, but final documentation, review and commit are pending. Do not report all nine weeks as complete.

| Week | Actual status | Remaining work |
|---|---|---|
| 01 | Theory/demo/actual local experiments completed; commit `90abb38` | Learner explains concepts in their own words; mentor acceptance |
| 02 | Backend access boundary and React tools page implemented in working tree; 176 backend tests and four frontend tests passed; production build passed | Finish documentation/status amendments, separate review, browser integration verification and scoped commit |
| 03 | Existing HR document RAG mechanisms preserved by migration | Claims corpus/metadata, React upload/Q&A/source UI, chunk-size comparison, ingestion/source tests |
| 04 | Existing hybrid retrieval/inspection primitives preserved | Frozen 12-question claims experiment, exact chunk IDs, one-change baseline/after evidence, inspection labels and latency; authentic adjuster questions are not supplied |
| 05 | Existing trace/review tools preserved | Redaction before write, self-contained replay, seeded 20-trace sample, human open coding/taxonomy/prediction workflow |
| 06 | Existing HR judge/evaluator preserved | Claims assertions, 25+ claims cases, regression provenance, blind-label sealing/order checks, judge iteration after real human labels |
| 07 | Existing HR agent/workflow preserved | Shared claims tools/status enum, ten-claim case mix, strict budgets including finalization, comparable race and measured verdict |
| 08 | Existing HR trajectory evaluator preserved | Claims valid/alternative paths, reality checks, metrics/gap, one measured mitigation and per-mode regression table |
| 09 | Local fictional claims MCP implementation and frozen evidence checkpoint committed in `5f6a4dc`; its 13 MCP tests passed; migrated imports remain tested | Integrate React inventory/trace, refresh current-source evidence after refactor, address remaining security/provenance gaps; actual third-party service and human peer evidence remain unavailable |

Existing HR work is useful implementation, not completion of insurance Task D. Local fictional claims examples must remain labelled fictional. Human/real-provider requirements cannot be manufactured by an agent.

## User authorization and working rules

The user explicitly authorized **all supplied weeks sequentially**, structural cleanup/refactoring, a backend with configuration/controllers/services, integrated React, tests, review, documentation and validated Git commits. They requested sensible defaults and no repeated design confirmations. The earlier Week 01-only gate is superseded by this later broad instruction, recorded in `AGENTS.md` under "Active authorization".

Read these files first:

1. `AGENTS.md`.
2. `.agents/skills/requirements-analysis/SKILL.md`.
3. `.agents/skills/implementation/SKILL.md`.
4. `.agents/skills/testing/SKILL.md`.
5. `.agents/skills/code-review/SKILL.md`.
6. `.agents/skills/demo-documentation/SKILL.md` and its demo template.
7. `requirements/README.md` and `requirements/week-01.md` through `week-09.md` (18 sections and stable acceptance IDs each).
8. `docs/architecture/current-architecture.md`, `execution-plan.md`, `repository-audit.md`, `traceability.md`, and `migration-roadmap.md`.

Apply the Postman API-engineer skill before API work; it and the API-testing/API-simulation skills were read in this session. No subagents were used or requested. Preserve prior evidence, databases, `.env`, `.venv` and unknown files. Do not fabricate real questions, human notes/labels, peer calls or improvements. Use small logical commits and one concise demo guide per week. Never claim a test ran if it did not.

## Repository, branch and commits

- Workspace: `C:\AI Practice\ollama-rag-fastapi`.
- Shell: PowerShell; Python: `.venv\Scripts\python.exe` (3.11.9).
- Current branch: **`feat/claims-weeks-02-09`**.
- Current HEAD: **`f4291fe`** `refactor(backend): separate controllers services and infrastructure`.
- Remote: `https://github.com/brahmareddy434/RagPipeline.git`.
- Relevant earlier commits:
  - `5f6a4dc` `feat(mcp): preserve validated claims integration before restructuring`.
  - `90abb38` `docs(week-01): record model experiments and mentor demo`.
  - `7f7e01c` `docs(architecture): establish weekly requirements and project workflows`.
- Only the original initial commit was previously pushed to main. New work in these branches has not been pushed in this session.
- Git commands need `git -c safe.directory='C:/AI Practice/ollama-rag-fastapi' ...` because of Windows ownership. Do not change global safe.directory.
- Existing Git email is `brahmareddybachu5@gmail.com`. No credential is needed in source. A GitHub token was exposed earlier in the conversation; do not reuse, copy or store it.

**The attempted Week 02 final patch/commit was interrupted before it executed.** A subsequent check confirmed HEAD is still `f4291fe` and the index is empty. Requirements/week-02.md and frontend/README.md still contain stale pre-implementation status. Resume this pending step after reviewing the working tree; do not assume that commit exists.

## Current backend structure

```text
backend/app/
  config/           settings.py, paths.py
  controllers/      documents.py, rag.py, tools.py, agents.py, mcp.py, pages.py, dependencies.py
  services/         ingestion.py, answers.py, evaluation.py, tools.py, mcp_host.py
  domain/           ports.py (uncommitted Week 02)
  agents/           loop.py, tools.py, workflow.py, memory.py
  rag/              loading.py, chunking.py, retrieval.py, prompts.py, grounding.py
  repositories/     vector_store.py
  infrastructure/   ollama.py, tracing.py, access.py; mcp/registry.py, wire.py
  legacy/           handbook.py, leave_totals.py, week6_assertions.py
  static/legacy/    inspection.html, agent.html
  bootstrap.py      dependency composition root
  schemas.py        existing Pydantic contracts
  main.py           app factory, lifecycle, middleware, router registration
app/__init__.py     one compatibility package-path shim to backend/app
frontend/           React application (uncommitted Week 02)
tests/              shared backend/integration tests, intentionally still at root
mcp_servers/        independently runnable policy/claims/gateway servers
course/             historical coursework, fixtures and runners
evaluation/         historical evaluation inputs and immutable evidence
config/             operator-controlled MCP configurations
requirements/       weekly specifications
docs/               architecture, demos, API/data/deployment plans
```

The migration moved source rather than copying the application. Active Python imports and root PowerShell runners were updated. Existing `app.main:app` startup works through the root package shim. Most old internal imports changed (for example `app.agent` -> `app.agents.loop`, `app.config` -> `app.config.settings`). The initial `src/claims_rag` architecture was adapted to `backend/app` for compatibility. Keep docs consistent with the current architecture.

Original HTTP routes are retained with `/api/v1` aliases. Existing examples include `/documents`, `/sources/{chunk_id}`, `/ask`, `/inspect`, `/tools/run`, `/tools/parallel`, `/evaluate`, `/agent/run`, `/workflow/run`, `/agent/race`, memory routes, `/mcp/tools`, and `/mcp/agent/run`. The new React client uses `/api/v1`. A session endpoint exists at `/api/v1/session`.

## Uncommitted Week 02 implementation

Tracked modifications verified at handoff:

```text
backend/app/config/settings.py
backend/app/controllers/agents.py
backend/app/controllers/dependencies.py
backend/app/controllers/documents.py
backend/app/controllers/pages.py
backend/app/controllers/rag.py
backend/app/main.py
backend/app/services/answers.py
backend/app/services/ingestion.py
backend/app/services/tools.py
tests/test_course.py
tests/test_week9_mcp.py
```

New untracked work to preserve and review:

```text
backend/app/domain/__init__.py
backend/app/domain/ports.py
backend/app/infrastructure/access.py
docs/demos/week-02-demo.md
frontend/index.html
frontend/package.json
frontend/package-lock.json
frontend/tsconfig.json
frontend/vite.config.ts
frontend/src/ (App, API client, request hook/state, tools screen, styles, tests)
tests/test_access.py
```

Backend behavior implemented:

- `create_app(settings=None)` supports isolated test application instances; module-level `app` retains existing startup.
- `ACCESS_MODE=local` accepts loopback clients only and rejects unapproved browser origins.
- Authenticated mode resolves a principal from `API_TOKEN_HASHES`, a mapping of SHA-256 token digests to `{tenant, role}`. Plaintext tokens are never configuration values.
- Roles are reader/writer/admin; document/memory writes require a writer/admin, clearing the whole index requires admin.
- Per-tenant document and memory Chroma collections and trace-log destinations; tenant identity is server-resolved.
- Trusted hosts and CORS are configurable; a simple per-tenant in-process request limit exists.
- Server-generated request IDs and safe validation responses that omit invalid input values.
- Broad `/course` static serving was replaced with `/course/guides`; private results/claims fixtures are no longer static assets.
- Built React `dist` is served at `/` when present at backend import/startup; legacy `/agent` remains.
- Small structural provider/retrieval/storage protocols in `domain/ports.py`; existing application services use some of these annotations.

Frontend behavior implemented:

- React 19.3.1, React DOM 19.3.1, React Router 7.18.5, TypeScript 7.0.2, Vite 8.3.6, plugin-react 6.2.1, Vitest 5.1.0.
- Shared typed fetch client uses `/api/v1`, Bearer header, omitted cookies, safe readable errors, cancellation and timeout fallback.
- Session check before feature routes render; token stays in memory only.
- Responsive overview/tools pages, labelled inputs, loading/error/success states and cancel support.
- React tools page calls `/tools/run`; its tests cover result rendering and recoverable error/retry.
- Vite proxies `/api` to `http://127.0.0.1:8000`, override with `API_PROXY_TARGET`.
- Four frontend unit/component tests exist. Playwright is installed as a dev dependency, but **no Playwright config or browser tests have been created or run**.
- `frontend/dist` and `node_modules` exist locally and are ignored. Package lock is intended for Git.
- The CSS still imports a Google font. The interrupted patch intended to remove that import so the UI has no external font request.

## Tests actually executed

| Check | Result |
|---|---|
| Original baseline under sandbox | 163 passed, eight MCP tests failed because Windows denied subprocess pipes; this was an environment failure |
| Baseline MCP rerun with process permission | 13 passed, three warnings, 36.82 seconds |
| Full suite after backend relocation/import fixes | **171 passed**, three warnings, 35.04 seconds |
| Targeted Week 02 access/course run | **23 passed**, two warnings, 14.63 seconds |
| Full suite with current Week 02 code | **176 passed**, three warnings, 34.44 seconds |
| `npm install --no-fund` | 96 packages added, 97 audited, zero reported vulnerabilities at that run |
| TypeScript/Vite production build | **Passed**, 27 modules; JS approximately 263.48 kB / 83.88 kB gzip |
| `npm test` | **4 passed** in two files, Vitest 5.1.0 |

Backend tests include actual local MCP stdio/HTTP subprocesses. Provider behavior in most application tests uses fakes/MockTransport. Frontend tests mock the client/fetch; they do not establish real browser-to-model integration. No new Week 02 live-model demo or browser check has been executed yet.

The warnings concern Starlette/httpx TestClient, an AnyIO alias, and a deprecated MCP HTTP-client alias. Do not claim production readiness from these passing tests.

## Exact immediate next steps

1. Run `git status --short` and inspect the current diff. Preserve every listed Week 02 file.
2. Finish the interrupted documentation patch:
   - Remove the Google Fonts `@import` from `frontend/src/styles.css`.
   - Replace `frontend/README.md`'s stale "not implemented" text with actual commands and token/proxy behavior.
   - Append a dated execution amendment to `requirements/week-02.md`; retain original criteria. Map W02-AC01–05 to source/tests and record the 176 backend/four frontend/build results accurately.
   - Update the Week 02 demo's verification paragraph; it currently mentions only the earlier targeted 23-test run.
   - Update demo index/traceability as appropriate; no claim that browser testing has happened.
3. Perform a separate self-review of the access boundary, dependency lifecycles, versioned compatibility, token handling, cancellation and tests. Address introduced Critical/High findings. This is not an independent human review.
4. Add browser/API integration verification against the real local application where practical. The existing Postman executable can run supported commands; do not fabricate unavailable CLI functionality.
5. Re-run affected tests/build after actual changes. Avoid re-running unchanged expensive suites merely to repeat their count.
6. Scan intended staged files for secrets; inspect `git diff --cached --check` and commit the Week 02 increment, suggested subject: `feat(week-02): add scoped API access and React tool workspace`.
7. Continue Weeks 03 through 09 sequentially using the plan below, documenting/testing/committing each meaningful increment.

## Remaining implementation plan

### Week 03: RAG and document UI

Reuse `services/ingestion.py`, `answers.py`, `rag/*`, vector repository and existing grounded answer validation. Implement React document upload/list/delete, grounded Q&A, and source viewing through authorized API calls. Preserve existing HTML until parity. Add source/version/edition provenance as needed, bounded parsing/upload checks, and failure tests. Compare two chunk sizes with frozen model/questions; save actual observed results. Use fictional corpus clearly labelled until authorized insurance documents are supplied. Never clear the user's existing index to run an experiment; use isolated collections/temporary storage.

### Week 04: retrieval experiment

Build a reusable claims benchmark with 12 questions and known chunk IDs, including four exact exclusion/form tokens. The required *real* adjuster-question provenance is unavailable: implement the runner and a labelled fictional demonstration, and leave authentic acceptance pending. Record baseline before changing one retrieval variable, use RRF(k=60) or top-25 cross-encoder reranking, save per-case ranks/inspection, classify misses using actual evidence, report hit-rate@3 and p50 latency. Do not combine improvements or invent gains.

### Week 05: privacy and trace analysis

Current `infrastructure/tracing.py` still writes whole records without redaction. Implement redaction before every trace sink, including nested/error/raw-model text, with explicit identifiers/field contracts and tests; do not promise perfect arbitrary-name detection. Capture sanitized prompts/version/chunks/scores/model/options/raw output/usage for self-contained replay. Add seeded sample/replay commands, a private authorized reader/review UI or CLI, frozen revision evidence and a human observation/taxonomy workflow. Do not populate supposed human notes or date predictions after a fix.

### Week 06: claims evaluation

Separate deterministic claim-ID/date/deductible/denial-clause assertions from one binary judge criterion. Create mode-tagged claims fixtures and a one-command evaluator; keep fictional data distinguished from two required real failed regressions. Implement label sealing/ordering/hash receipts, prompts v1/v2, disagreement selection and prediction workflow. **Human blind labels are missing.** Do not run a judge then invent human labels or report agreement without them. The existing HR labels and sealed files must stay HR and byte-preserved.

### Week 07: claims agent/workflow

Define typed claims and tool arguments (status enum), a read-only claims repository and tools with distinct jobs. Reuse the hand-built loop through a domain-specific composition; implement the same task as a genuine fixed sequence using identical tools/model/output. Add ten fictional claims with at least three dependent exclusion cases, clearly labelled. Enforce iterations/tokens/cost/deadline across model decisions, tools, memory/compression and finalization. Existing loop still has budget audit gaps. Capture clean termination and complete per-call usage. Run a real ten-case comparison when local model capacity permits; report all eight numbers and an honest verdict.

### Week 08: trajectories

Define expected sequences and legitimate alternatives for the ten claims before running. Validate actual claim/clause existence, count outcome versus path passes, tool choice, argument validity, step efficiency, cost p50/max. Show a measured right-answer/wrong-path example if observed; do not construct fake model evidence. Pick one actual top-mode mitigation, freeze other variables, measure before/after and numeric price, then report all mode regressions. Keep older HR results labelled historical.

### Week 09: MCP integration and evidence

Existing local policy and claims servers, gateway scopes, discovery, raw wire and error recovery already exist and are checkpointed. Add the React tools inventory/run trace/error view. Current-source evidence runners were updated during migration to snapshot `backend/app/agents/loop.py`, `services/mcp_host.py` and `infrastructure/mcp/registry.py`; ensure any textual model-location description is also current. Freeze the agent after all baseline wiring, then prove adding server two is config-only. Keep old snapshots untouched. Confirm tools/list counts from replies, raw fields, recoverable errors and exactly five risk-note lines. A separate SDK client is not another person's agent; real peer evidence and personal wire review remain pending.

### Final integration/cleanup/deployment work

Complete concise `docs/demos/week-03-demo.md` through `week-09-demo.md`, requirements amendments and traceability. Avoid competing full guides: historical guides may become short links after safe migration. Add meaningful backend/frontend/API/browser checks, CI and containers/startup/rollback docs where practical. Preserve `.env`, `.venv`, Chroma, uploads, backups and immutable reviewed evidence. Review references/uniqueness/Git recovery before deleting files; remove only demonstrably redundant/generated content. Do not bulk-delete coursework merely for visual tidiness.

## Commands and infrastructure

From repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
.\.venv\Scripts\python.exe -m pytest -q --tb=short
.\.venv\Scripts\python.exe -m app.services.mcp_host --list
```

From `frontend`:

```powershell
npm ci
npm run dev
npm run build
npm test
```

Existing Ollama is at `http://localhost:11434`; observed version 0.40.14. Installed chat models include `llama3.2:3b` and `qwen3:4b`; embeddings include `nomic-embed-text:latest` and `embeddinggemma:latest`. The safe settings read observed llama3.2:3b and nomic-embed-text:latest active. Do not print the whole `.env`. Local inference has operating costs; reference token rates are hypothetical, not invoices or current vendor prices.

Postman CLI observed version **1.74.0**. Under the sandbox, even version/help may fail because a managed Private Cloud manifest is unreadable. Outside the sandbox, `postman --version` works but **`postman status` is an unknown command** in this installation. That was checked, not assumed. No new Postman collection run succeeded in this increment. Reuse `docs/postman/Week9_MCP_Demo.postman_collection.json` where useful; inspect command-specific help before further use.

Windows may block new directories, Git writes, npm network access and subprocesses despite the user's broad project authorization. Use the platform's required escalation with a concrete reason when an operation fails. Do not repeatedly ask for business/design confirmation. `apply_patch` works for most files, but new directories inside migrated backend sometimes required a scoped elevated `New-Item`. Vite and MCP tests required process permission. Node 24.22.1 / npm 11.19.1 were observed.

No long-running server or test session is known to remain active from this work; check actual ports/processes before starting one. Do not stop unrelated user services.

## Historical evidence and unresolved risks

`evaluation/week9/**` is intentionally `-text` in `.gitattributes`. Its raw JSON-RPC lines/snapshots contain CRLF bytes; whitespace normalization would invalidate hashes. The checkpoint used whitespace checks excluding these immutable raw artifacts. Never rewrite them to make `git diff --check` quiet.

The original audit (`docs/architecture/repository-audit.md`) remains historical. Week 02 starts addressing identity/tenant/static exposure, but source redaction, strict agent budgets, MCP citation resolution, real-provider auth/provenance and production deployment still need implementation/review. Update the audit resolution status with evidence as fixes land. A single-worker token/rate-limit implementation does not establish enterprise OIDC, distributed rate limiting, malware scanning, backup/restore or production certification.

## Suggested continuation prompt

> Continue the authorized Weeks 01-09 implementation in this same workspace. Read `docs/CODEX_HANDOFF.md`, `AGENTS.md`, all five `.agents/skills/*/SKILL.md`, and the weekly requirements. Preserve the current uncommitted Week 02 code. Start by finishing its documentation, review and scoped commit, using the recorded test results honestly. Then implement Weeks 03-09 sequentially, with the structured backend and React frontend, real checks, concise weekly demos and logical commits. Use sensible defaults without repeated design confirmations. Never invent human grading, real claims provenance, peer calls or measured improvements. Report remaining external acceptance requirements explicitly.
