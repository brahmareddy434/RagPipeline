# Deployment, services and cost decisions

Status: local coursework only; no production deployment authorized or provisioned.

| Concern | Current / proposed decision | Cost and unresolved input |
|---|---|---|
| LLM and embeddings | Keep Ollama for local work | No vendor per-token charge for local calls; hardware, energy and operating costs remain. Reference USD figures in evaluations are estimates, not invoices. |
| Vector storage | Keep local Chroma initially | Local disk/backup costs; remote capacity and operating model pending |
| Relational metadata | PostgreSQL candidate when identities/versioning require it | Hosting, retention and availability requirements needed before a quote |
| Frontend | React TypeScript SPA built separately | Build/static hosting cost depends on deployment choice |
| Original documents | Local adapter for development; encrypted object storage candidate for production | Retention, size and data residency requirements pending |
| Identity | Organization OIDC provider preferred | Provider/tenant, roles and licensing not supplied |
| Hosting / monitoring | Modular monolith, structured logs and health endpoints | Target cloud, GPU/CPU sizing, concurrency/SLO, data residency and telemetry budget unspecified |

No priced paid service is selected. Obtain current provider quotes before spending; do not present guessed cloud totals as a budget.

## Production release gates
Resolve audit High findings; verify identity/tenant isolation and redaction; private evidence storage; TLS termination and encrypted stores/backups; secrets injected through the deployment platform; explicit upload and LLM concurrency limits; measured timeout/cost budgets; retention policy; restore rehearsal and rollback plan.

## Packaging plan
After backend relocation is validated, add pinned reproducible Python installs, a non-root backend Docker image, frontend build, health/readiness separation, and environment samples without credentials. Keep Ollama/model files and persistent stores in separate volumes/services. Do not share a local embedded Chroma directory between arbitrary worker processes.

CI will run backend unit/integration tests, lint/type checks introduced with code boundaries, frontend checks once React exists, dependency/secret scans and targeted API contract checks. Live Ollama evaluation is explicit and separate from deterministic PR tests; use appropriate fixtures and state whether results are mock or live.

## Rollback
Release tagged immutable images and versioned config. Migrations use expand/contract and verified backups; never reset/delete live collections as rollback. Restore prior image/config, retain previous embedding collection until verification, and replay only authorized idempotent operations. The exact RPO/RTO and performance targets require owner decisions before production acceptance.
