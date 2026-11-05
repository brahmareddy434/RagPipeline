# Current architecture

The 2026-11-05 authorization covers all supplied weeks and structural migration. The initial proposed `src/claims_rag` layout is superseded by `backend/app` to preserve `app.main:app` with one root package-path shim.

Requests flow through feature controllers to application services, injected provider/retrieval/repository dependencies, then validated response schemas. `bootstrap.py` is the composition root. Legacy HR rules remain explicit in `legacy`; claims features must not borrow HR evaluation results.

The migration preserves original routes and adds `/api/v1` aliases. It splits six controllers and three existing services, centralizes repository-relative paths, and updates active course/test imports. No database was moved, cleared or re-embedded. MCP fixture servers remain independently runnable at `mcp_servers/`.

Historical experiment snapshots are intentionally immutable, even when their old paths differ. New experiment manifests use current paths. Never recompute historical hashes from subsequently refactored code.

Validation: all 171 original tests passed after migration, including real stdio/HTTP MCP tests. Two legacy import forms were corrected before acceptance. This checkpoint does not claim to resolve pre-existing security findings; subsequent increments address those boundaries.
