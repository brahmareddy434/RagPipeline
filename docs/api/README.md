# API baseline and versioning plan

Current routes are defined in app/main.py; runtime discovery is /openapi.json. No /api/v1 router exists yet. This inventory is a source-review baseline, not a claim that every endpoint was live-tested.

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
