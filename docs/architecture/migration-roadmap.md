# Migration and product roadmap

## Execution gate
The user explicitly requires **Implement Week 01** before the weekly implementation workflow. Initial repository audit, requirements, skills and design are authorized now. Week 01 remains theory-only even after that instruction. A separate requested architecture-migration increment may reorganize existing code; do not treat theory scope as permission to build all nine weeks.

## Sequence
| Increment | Work | Exit condition / rollback |
|---|---|---|
| 0: foundation (this pass) | Audit, nine draft requirement specs, skills, architecture, traceability, cache cleanup | Artifacts reviewed; existing source/contracts unchanged; requirements marked draft |
| A: packaging | Establish backend package, relocate tests/resources, centralize paths, retain thin old entry points | Full suite and current start/eval commands work; revert packaging commit without touching persisted data |
| B: boundaries | Split API routers, use cases, provider/storage/tool ports and evidence resolver | API contract parity, lifecycle/timeout checks, no new provider calls in server modules |
| C: security foundation | Identity integration, tenant scope, pre-write redaction, private evidence, quotas | Negative authorization/leakage tests pass; deployment remains blocked until owner choices resolved |
| D: React parity | Separate React application using centralized API client and feature views | Existing document/ask/inspect/run/MCP journeys work; accessibility and error states verified before retiring HTML |
| E: claims requirements | Implement requested weekly Task D gaps against frozen fixtures and authorized real samples | Each week's acceptance evidence; no fabricated human labels or historical measurements |
| F: deployment | Container/CI packaging, environment configuration, backups, restore and rollback | Reproducible builds and environment-specific release checklist; explicit publish/deploy instruction |

Architecture increments are proposed, not completed or auto-approved as weekly features.

## Week roadmap
| Week | Scope | Existing reusable capability | Gap for supplied Task D |
|---|---|---|---|
| 01 | LM foundations; no code | course/guides/01_language_models.md | Fresh learner explanations and small experiments, with dated model/cost assumptions |
| 02 | structured output and safe tool use | OllamaClient, models, tools | React integration and production identity boundaries when relevant |
| 03 | document RAG and citations | loader, chunker, store, retriever, answer validation | Approved insurance corpus, version metadata, access isolation and source resolution |
| 04 | one retrieval change on 12 questions | inspect, BM25/RRF, evaluation | Real adjuster questions with known chunk IDs; measured baseline and isolated change |
| 05 | 20 random traces and human coding | trace logger, sample/review tooling | Redaction before write, self-contained replay, authentic human notes and committed prediction |
| 06 | validate binary judge | eval scripts, sealed labels pattern | 25+ claims cases, 25 new blind human labels, claims assertions, actual disagreement-driven iteration |
| 07 | race same 10 claims | bounded loop and fixed workflow | Claims tools/status enum, shared task/contract, 3 dependent cases, strict budgets and complete usage |
| 08 | 10 claims trajectory cases | trajectory runner and guards | Claims paths/valid IDs, one mitigation, measured price and full regression table |
| 09 | MCP extension | stdio/HTTP discovery, two fixture servers, gateway | Real platform provenance/auth, peer agent call, personal wire annotations, production isolation |

## Change and evidence rules
- Preserve the old HR evidence as HR. New claims results must identify corpus, question IDs, model, configuration and code revision.
- Freeze approved requirements; amendments require dated explanation and impacted acceptance IDs.
- Never delete unknown/untracked files as cleanup. Check references, content uniqueness, Git tracking and recovery path first.
- Relocate a dataset or package once; use temporary compatibility imports/links only with a removal criterion.
- Source snapshots in reviewed Week 9 evidence remain immutable even when active source moves. Future experiments get new evidence, not rewritten historical hashes.
