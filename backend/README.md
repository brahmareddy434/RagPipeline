# Backend migration destination

The active backend is currently ../app; start it from the repository root using the existing scripts. This directory records the migration destination and does not contain a second implementation.

Planned: an installable claims_rag package under src/, feature API routers, use cases, domain ports, infrastructure adapters, agent/RAG modules and tests. See ../docs/architecture/target-architecture.md and migration-roadmap.md.

Move code only in an authorized migration increment, with entry-point/import compatibility, resource paths, fixture resolution and full regression checks. Preserve local Chroma data and reviewed evidence. Do not change app.main:app or root PowerShell commands until replacements and compatibility behavior are demonstrated.
