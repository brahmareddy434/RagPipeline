---
name: implementation
description: Implement an explicitly requested week across the existing Python backend and planned React frontend while preserving contracts, evidence and staged migration.
---

# Implementation

Read root AGENTS.md, the approved/requested weekly requirements, architecture and current code before changes. Initial implementation waits for "Implement Week 01"; Week 01 remains theory-only. Clarify only critical missing business decisions; do independently authorized work meanwhile.

Follow the migration roadmap. Active code is still app/, tests/, mcp_servers/ and course/ until a migration is implemented. Do not copy the whole app into backend/ or break app.main:app, root scripts, resource paths or existing screens. Use a modular monolith with narrow ports only at provider/storage/tool/evidence/telemetry boundaries. Build dependencies in one composition root.

Backend changes: keep HTTP translation in routers, orchestration in use cases, domain rules independent of FastAPI/Chroma/MCP SDK, and provider/persistence details in adapters. Enforce authorization at the server and scope retrieval/source/memory operations. Redact before trace writes; attach correlation IDs and map errors safely. Handle lifecycle cleanup, bounded retries, absolute deadlines and all model usage, including finalization.

Frontend changes belong in frontend/: reusable accessible React feature components, routing, a central typed API client, explicit loading/error/empty/success states and cancellation. Implement only the requested feature and prove its backend contract. Do not retire current HTML until parity is demonstrated. Never invent frontend test/build success before a React app exists.

RAG/agent changes reuse loaders, chunkers, ranking, grounding and bounded orchestration. Treat model/tool/document text as untrusted. Keep models in the MCP host, server configuration operator-controlled, tools discovered dynamically and resources app-attached. Keep credentials out of config snapshots and logs.

Freeze code/config/data during graded before/after experiments; change exactly the permitted variable. Preserve reviewed evidence and label snapshots. Do not manufacture a measured improvement.

Before a library is added, document the missing capability and why an existing component is insufficient. Update relevant requirements/traceability, tests and demo instructions; apply review/testing skills before the authorized validated commit. No cloud deployment or force push is implied.
