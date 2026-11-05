# Week 01 — initial mentor review

Status: architecture/requirements prepared; implementation has not begun. Await **Implement Week 01**. The week itself is theory-only.

## Objective and work completed
Understand prediction, tokens/context, embeddings, sampling, model types, hallucination and cost. This initial pass audited the existing project and prepared draft requirements, architecture, traceability and reusable skills. It introduced no backend feature, React screen, database migration or AI/RAG behavior.

## Prerequisites and startup
Open the repository in an editor. No API key, service, database or frontend startup is needed for the initial design/theory presentation.

To show prior work optionally: start Ollama, run `./run_week9.ps1 -Serve` from the root and open `http://127.0.0.1:8003/docs`. That is the existing Week 9 local application, not a new Week 01 deliverable. No React startup command exists yet.

## Mentor walkthrough
1. Open `requirements/week-01.md`: objective, stable acceptance IDs and no-code scope.
2. Open `docs/architecture/repository-audit.md`: existing FastAPI/Ollama/Chroma, HTML UI and HR-versus-insurance gap.
3. Open `docs/architecture/target-architecture.md`: proposed modular backend, React frontend, narrow provider/storage interfaces and dependency injection.
4. Open `docs/architecture/traceability.md`: separate reusable mechanisms from pending claims data, blind human labels and peer evidence.
5. Open `.agents/skills/`: the five reusable project workflows.
6. Read `course/guides/01_language_models.md` for theory. Learner observations and explanations remain to be completed; generated notes are not presented as personal experiments.

## Requests, screens and expected output
No new API request/response or UI screen applies. Expected output is a clear proposed architecture and draft Week 01 specification. Existing API examples/screens are in the [Week 09 guide](../DEMO_Week9_MCP.md).

## Decisions, tests and limitations
Retain a modular monolith and migrate in stages with compatibility checks. A fresh baseline produced **171 passing tests**, with three dependency deprecation warnings. This verifies current behavior, not production security or a React application. See the [initialization report](../architecture/initialization-report.md).

Identity provider, hosting/SLOs, real claims service, authorized questions/traces, blind human labels and peer-agent call remain pending.

## Short explanation
“We already have a working local RAG and agent application. I audited it, recorded the claims requirements and planned a staged migration to a modular backend and React frontend. Week 01 is about understanding the model, so the next work is explanations and small experiments. Existing regression tests give us a baseline for later changes.”
