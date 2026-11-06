# Week 09 — Add a claims MCP server through configuration

Status: draft v0.1; approval pending. Source: user requirements, 2026-11-05. Initial extraction; no approved prior specification changed.

## 1. Week and objective
Prove tool discovery, host/server separation and config-only second-server integration.

## 2. Business requirements
Allow a reviewed claims-platform capability to be connected without a new agent code release.

## 3. Functional requirements
Policy server baseline; claims status and notes server through config; actual tools/list names/counts; raw initialize/list/call with field annotations; zero agent diff; one own-tool docstring/error rewrite with same-failure transcripts; five-line risk note.

## 4. Non-functional requirements
Preserve prior behavior, reproducible evidence, safe failures and maintainable boundaries. High audit findings block real-data production release; no automated coverage decision or payout is authorized.

## 5. Technical requirements
Use standard SDK stdio/HTTP transports; paginated discovery, schema validation, namespaced routing and recoverable tool errors. Resource exclusions are app-attached, never forced into a tool.

## 6. Backend requirements
Host owns model calls; reusable servers expose data/capabilities; operator-controlled config and lifecycle cleanup. Establish baseline after initial MCP wiring, then freeze agent sources for server-two proof.

## 7. Frontend requirements
React exposes the configured discovered-tool inventory, raw `tools/list` replies, bounded MCP host run and trace/error details. Existing Swagger and HTML/CLI demos remain available for protocol-level inspection.

## 8. Database requirements
No new claims source of truth; fictional fixtures until real platform configured. Evidence capture private and sanitized.

## 9. AI Agent requirements
Use discovered metadata, not a hand-coded list after connection. Unknown IDs, denied scope and network unavailability must be distinct observations.

## 10. RAG requirements
Reuse policy retrieval and attached exclusions resource with validated citations; do not perform coverage judgment inside an MCP server.

## 11. API requirements
Current /mcp/tools and /mcp/agent/run provide host entry points; SDK wire exchange is separate from those HTTP routes.

## 12. Security requirements
Review server author/reach/logging/token impact before real connection; secure remote auth and TLS; stdio is not an OS sandbox. Never commit tokens/raw real claimant wire data.

## 13. Performance requirements
Record discovery/run costs and timeouts as observed; no claim that MCP improves answer accuracy by itself.

## 14. Dependencies on previous weeks
Existing bounded loop, tool observations, policy search and runtime configuration.

## 15. Acceptance criteria
- **W09-AC01**: A real model trace shows a successful claims-server tool call discovered through config.
- **W09-AC02**: Source snapshots and actual git diff prove zero agent changes between server-one baseline and server-one-plus-two; retain config diff.
- **W09-AC03**: Tools/list replies prove before/after count and exact names; exclude host-local finish.
- **W09-AC04**: wire.json captures actual initialize, initialized, tools/list and tools/call; explain every top-level field and host model location; student personally reviews annotations.
- **W09-AC05**: One own-server docstring and recoverable error change are compared using the identical failing call with honest model transcripts.
- **W09-AC06**: risk_note.md contains exactly five lines: author, reach, logs, stolen-token impact and decision.
- **W09-AC07**: Optional gateway uses one front door, one audit line per call, and demonstrates notes denial with status still allowed.
- **W09-AC08**: A separate person's agent calls the reusable own server; SDK-client demonstration alone is not that human peer evidence.

## 16. Test scenarios and traceability
tests/test_week9_mcp.py exercises real local SDK servers, pagination, errors, raw wire, HTTP, independent client and gateway scopes. Production tenancy and actual third-party OAuth remain unverified.

- W09-AC01 -> planned W09-V01: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.
- W09-AC02 -> planned W09-V02: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.
- W09-AC03 -> planned W09-V03: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.
- W09-AC04 -> planned W09-V04: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.
- W09-AC05 -> planned W09-V05: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.
- W09-AC06 -> planned W09-V06: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.
- W09-AC07 -> planned W09-V07: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.
- W09-AC08 -> planned W09-V08: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.

Reusable source/evidence: app/mcp_registry.py, app/week9.py, mcp_servers/*, config/mcp.*.json; evaluation/week9/submission.

Current status: **Local Task D MCP mechanics/evidence, tested integration and React inventory/run trace delivered.** Actual platform credentials/data, personal wire annotation, peer call and production isolation remain pending. See [cross-week traceability](../docs/architecture/traceability.md).

## 17. Out-of-scope items
Pretending local fixtures are the real platform; inventing peer approval/handwritten annotations; claiming lookup recovery means correct final answer.

## 18. Risks and assumptions
Actual claims URL/provenance/token scopes and human peer call are absent. Gateway is a process-scoped local token demo. Historical zero diff applies to its frozen baseline, not future refactors.

Amend approved scope using [change control](README.md).

## Execution amendment - 2026-11-06
User-authorized integration adds claims benchmark/run APIs and React MCP inventory plus discovered-tool run traces while retaining the separately reviewed Week 09 local SDK evidence and zero-agent-diff snapshot. Local MCP fixture and gateway behavior are covered by integration tests. Real platform credentials/data, personal annotation and a separate person's peer call remain pending.
