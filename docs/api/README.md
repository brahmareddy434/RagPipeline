# API baseline and versioning plan

Current routes are defined in `backend/app/controllers/`; runtime discovery is `/openapi.json`. Original paths and `/api/v1` aliases use the same handlers. The table below retains the historical baseline; current additions are listed here.

| Added route under `/api/v1` | Contract |
|---|---|
| GET `/session` | Server-resolved tenant/role; local loopback or configured token digest |
| GET `/traces`, `/traces/{uuid}` | Tenant-private bounded redacted trace window; missing IDs return 404 |
| GET `/claims/fixtures` | Ten explicitly fictional claim choices and three typed tools |
| POST `/claims/run` | `{claim_id, approach: agent/workflow/race, budget}`; shared grounded run contract, stop reason, usage and evidence |
| GET `/claims/evaluation` | Thirty-case fictional assertion report; no private labels |
| GET `/claims/benchmarks` | Completed baseline/mitigation summaries; partial attempts are not aggregated |
| GET `/claims/benchmarks/{phase}/{approach}/{case_id}` | Fixed phase-name pattern plus exact approach/case checks; no arbitrary file access |

Document/source calls enforce tenant isolation. Document replacement changes content-version IDs and invalidates old source links (404). Tool/resource citations resolve inside the returned run evidence; their URL is empty instead of pointing at Chroma. Static coursework is limited to `/course/guides`.

Use `docs/postman/Claims_Workbench.postman_collection.json` for read-only local contract checks, with `--no-report-events`. Live results are recorded in the completion report. API errors use safe detail strings/validation fields and request IDs; client cancellation stops waiting, while backend agent budgets bound ongoing work.

| Current route | Responsibility / compatibility requirement |
|---|---|
| GET /health | model availability, collection and chunk count |
| GET/POST /documents | list/ingest documents; preserve single and multi-file request support |
| DELETE /documents and /documents/{source} | clear/delete indexed content; add permissions before real deployment |
| GET /sources/{chunk_id} | scoped citation resolution required; currently Chroma-only |
| POST /ask, /inspect, /evaluate | grounded answer, retrieval inspection, retrieval metrics |
| POST /tools/run, /tools/parallel | structured tool execution |
| POST /agent/run, /workflow/run, /agent/race | existing HR loop/workflow comparison |
| GET /agent/tools; GET/POST/DELETE /agent/memory routes | catalogue and session facts; tenant auth pending |
| GET /mcp/tools; POST /mcp/agent/run | insurance MCP discovery and run |
| GET /, /agent; /course static mount | existing UI/reading pages; static exposure needs restriction |

Target: feature APIRouters under /api/v1 with legacy aliases to the same handlers during a documented migration period. Preserve status codes and DTOs until a versioned contract change is agreed. Add correlation IDs and a consistent safe error envelope through centralized mapping; do not expose provider stack traces or tokens.

Authentication, rate limits and authorization must protect both old aliases and new routes. Configure CORS by environment. Browser route guards are not authorization.

The existing Postman collections live in docs/postman/. Reuse them where applicable; do not claim CLI success from a collection file's existence. The earlier CLI check could not use status; evaluate installed CLI capabilities before adopting a CI command.

Before migration: capture representative request/response fixtures with sensitive data removed; verify upload errors, source lookup, abstention, timeout, agent stop reasons and tools/list counts. Generated OpenAPI snapshots can be reviewed contract artifacts; ordinary run logs stay ignored.
# Live Week 8/9 mentor demonstrations

All routes below also have the `/api/v1` prefix and use the existing access boundary. They operate on fictional data only. Query length is 2–2,000 characters; variants are closed enums, with no client-supplied config paths or budgets.

| Route | Input | Result |
|---|---|---|
| `POST /claims/demo/run` | `task`, `variant: before|after`, optional `injection: boolean` | Grounded `run`, original task, diagnostics, exact prompt change, trace ID. Requires exactly one existing CLM-2026 claim ID. |
| `GET /mcp/demo/tools` | `variant=before|after` | Actual tools/list replies, names and count. Before selects policy-only; after adds claims. |
| `POST /mcp/demo/run` | `task`, `variant: before|after` | Actual MCP discovery and host `run`, task, variant, trace ID. Example claim: CLM-2024-88120. |

Unknown IDs or missing claim selection return 400; invalid request shapes/profile names return 422. Each model arm has a 180-second, 32,000-token, $0.03 reference-cost ceiling; Week 8 allows six steps and Week 9 four. MCP setup precedes the model-run deadline. Provider failures within a run appear in its stop reason; an HTTP 200 does not establish answer quality. Costs are reference estimates, not an Ollama invoice. Injection marker absence is not a security verdict.

Run local contract checks with `postman collection run docs/postman/Mentor_Demos.postman_collection.json --no-report-events`. For actual model responses, use `.venv/Scripts/python.exe -m course.mentor_demo_smoke logs/<new-directory>`; existing output directories are rejected to preserve prior attempts.
