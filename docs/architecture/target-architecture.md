# Proposed architecture — modular monolith

Status: initial design for review. No runtime migration has been applied. Insurance claims is the target product domain; existing HR coursework is retained as a separate legacy training dataset.

## Decisions
Retain Python/FastAPI, Pydantic, Ollama and Chroma initially. Use a single deployable backend with feature routers and a composition root. Extract interfaces only at provider, persistence, tool-registry, evidence and telemetry boundaries; avoid base-class hierarchies and generic repository frameworks.

The target React UI is a TypeScript SPA using Vite, with routing and one API client. SSR is not currently needed for an authenticated internal claims tool. Pin compatible package versions when implementation begins. React documents the SPA build-tool approach and its routing/data-fetching tradeoffs in its [official guide](https://react.dev/learn/build-a-react-app-from-scratch). FastAPI supports feature modules through [APIRouter](https://fastapi.tiangolo.com/tutorial/bigger-applications/).

## Target tree (planned, not current runtime)
```text
backend/
  pyproject.toml
  src/claims_rag/
    api/v1/           # routers, request/response DTOs, exception mapping
    application/      # use cases, provider/storage/tool ports, policies
    domain/           # claims, documents, evidence, runs, access context
    infrastructure/   # Ollama, Chroma, metadata store, files, telemetry, MCP client
    agents/           # bounded orchestration and fixed workflow
    rag/              # ingestion, chunking, retrieval, context, grounding
    bootstrap.py      # construct dependencies and application lifecycle
  mcp_servers/        # thin reusable tool/resource servers
  tests/
frontend/
  src/
    app/              # router, providers, layouts
    features/         # documents, ask, inspection, runs, evaluation, MCP tools
    components/       # shared accessible primitives
    lib/api/          # typed HTTP client, request cancellation, errors
requirements/         # versioned Week 01–09 requirements
docs/                 # architecture, api, database, deployment, demos
.agents/skills/       # five reusable workflows
scripts/              # setup/start/evaluation commands
.github/workflows/    # CI once packaging is validated
```

Root app/, tests/, course/ and mcp_servers/ remain active until staged relocation. Do not duplicate source into backend/. Protect existing app.main:app and CLI entry points with tested compatibility wrappers during migration.

## Responsibilities and dependency direction
API -> application use cases -> domain contracts. Infrastructure implements those contracts; bootstrap assembles them. Domain code must not import FastAPI, Chroma or the MCP SDK. React communicates only with the HTTP API.

| Boundary | Small contract | Existing code to adapt |
|---|---|---|
| Model provider | structured generation and usage; embedding port separate | app/ollama_client.py |
| Document storage | scoped read/write, metadata and version lookup | app/vector_store.py, document_loader.py |
| Retrieval | query + access context -> ranked evidence | app/retrieval.py |
| Agent tools | catalogue/schema + execute -> observation | app/agent_tools.py, app/mcp_registry.py |
| Evidence | resolve citation/provenance for documents, tools and resources | app/answer_quality.py, /sources |
| Telemetry | redact then append trace/audit event | app/trace_logger.py |
| Use cases | ingest, ask, inspect, run agent/workflow | app/services.py, app/agent.py, app/workflow.py |

SOLID application: small feature services own one responsibility; new adapters implement narrow ports; contract tests establish substitutability; consumers request only needed capabilities; the composition root supplies dependencies. Do not introduce abstractions merely to create more files.

## Request flows
1. Authenticate and derive tenant/permissions on the server.
2. Validate input, assign correlation/run ID, enforce request limits.
3. Retrieve only authorized, edition-matched evidence; construct a bounded context.
4. Run a fixed workflow or bounded agent through the shared provider/tool interfaces.
5. Validate structured output and citation provenance; represent uncertainty explicitly.
6. Redact identifiers before trace/audit writes; return authorized citations and usage.

MCP tool descriptions and outputs are untrusted inputs. Server config is operator-controlled; the model cannot choose executables, endpoints or tokens. Resources are app-attached context, tools are model-selected operations, and prompt templates are user-selected. Keep the model in the host.

## Frontend plan
Views: document upload/list; grounded Q&A; retrieval inspection; agent/workflow comparison; evaluation evidence; MCP discovery/trace.
Each view must handle loading, errors, empty results and success; keyboard navigation, focus management and labelled controls are acceptance checks. Begin with local state and a centralized HTTP client; add server-state caching only when measured duplication justifies it. Do not store tokens or claim notes in browser persistence by default.

## Security and reliability gates
Identity provider and production hosting are pending owner decisions. Use existing organizational OIDC if available; do not build password storage. The local development mode must be explicit, loopback-bound and limited to fictional data.

Enforce authorization consistently on retrieval, raw source reads, memory, evidence exports and tools. Redact before persistence; restrict public static assets. Apply end-to-end deadlines, bounded retries only for safe operations, and concurrency limits. Introduce durable ingestion jobs only when request duration/volume justifies them. No real coverage decision or payout action is authorized by the present requirements.

## Data and infrastructure
See [database plan](../database/README.md) and [deployment/cost plan](../deployment/README.md). Preserve Chroma during initial migration; evaluate PostgreSQL for normalized metadata when identities, document versions and durable runs are implemented. No new cloud service, model subscription or database is provisioned in this pass.
