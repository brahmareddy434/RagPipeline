# Persistence design

## Current state
Chroma persists document chunks/embeddings and separate vector memory locally in data/chroma. Source files are parsed but VectorStore does not retain originals. JSON fixtures supply fictional HR and claims records; JSONL files record runs. There is no relational metadata schema or migration tool in the application.

## Proposed relational metadata (implementation pending)
| Entity | Key and ownership | Purpose |
|---|---|---|
| tenants / principals / memberships | tenant_id; identity-provider subject; role association | authorization context, no local password table |
| documents | document_id, tenant_id, content hash | logical document identity and scoped ownership |
| document_versions | version_id, document_id, edition/effective dates, storage key | immutable policy wording versions |
| chunks | chunk_id, version_id, ordinal, offsets, embedding revision | citation mapping and vector provenance |
| ingestion_jobs | job_id, tenant_id, idempotency key, status | durable ingestion only when introduced |
| runs / run_steps | run_id, tenant_id; step sequence | redacted traces, budgets and usage |
| eval_cases / eval_runs / human_labels | immutable dataset/version/run IDs, label receipt | reproducible experiments and provenance |

Keep external claim status/notes in their owning system; only persist a minimal authorized reference or redacted evidence when required. A local fixture is not the source of production truth.

Use foreign keys, unique (version_id, ordinal), unique scoped idempotency keys, and indexes supporting tenant+document, run time and status queries. Avoid storing vectors in two systems. PostgreSQL metadata plus existing Chroma is the initial candidate; consider pgvector only after a measured need and migration comparison.

Tenant filters must apply before retrieval and again before evidence resolution. Policy edition/date metadata is part of the retrieval contract, not an instruction left to the model.

## Migration and recovery
No schema or data is changed in this pass. Introduce migration tooling with the first relational implementation, baseline test fixtures, backup/restore verification and expand/contract changes. Retain old vector collections during re-embedding; never silently replace an embedding model in a populated collection. Original documents require an encrypted filesystem/object-store adapter and explicit retention/access policy before real ingestion.

Redaction and replay have competing needs: preserve consistent pseudonymous references and exact prompt/chunk/version information, while keeping any reversible mapping outside trace logs under separate access controls. Document which original values cannot be reconstructed from a sanitized trace.
