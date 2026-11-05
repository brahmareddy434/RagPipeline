# Week 02 — Prompting, structured output and tool calling

Status: draft v0.1; approval pending. Source: user requirements, 2026-11-05. Initial extraction; no approved prior specification changed.

## 1. Week and objective
Build on existing provider calls to produce validated JSON and execute a safe real action.

## 2. Business requirements
Provide predictable machine-readable answers and auditable tool execution.

## 3. Functional requirements
Clear prompt anatomy with examples; schema-constrained outputs; bounded validation/retry; calculator/lookup action; parallel calls where independent; safe failure on malformed input.

## 4. Non-functional requirements
Preserve prior behavior, reproducible evidence, safe failures and maintainable boundaries. High audit findings block real-data production release; no automated coverage decision or payout is authorized.

## 5. Technical requirements
Reuse Pydantic and OllamaClient; evaluate instructor only if a demonstrated gap needs it. Cover zero/few-shot, task decomposition and self-consistency without exposing private reasoning or requiring expensive extra calls.

## 6. Backend requirements
Provider port, structured-output use case, tool validation/dispatch, safe exception mapping and bounded provider timeouts.

## 7. Frontend requirements
In the requested UI increment, a React tool/answer view uses the centralized API client and shows loading, validation errors, result and usage.

## 8. Database requirements
No new database needed for calculator/fictional lookup. Explicitly separate fixture storage from future claims sources.

## 9. AI Agent requirements
The model selects a tool/arguments; trusted Python validates and executes. No autonomous loop is required yet.

## 10. RAG requirements
No retrieval implementation added by this week.

## 11. API requirements
Preserve existing /tools/run and /tools/parallel contracts; version any changes using the API migration plan.

## 12. Security requirements
Secrets from environment/platform; no arbitrary Python execution; reject unsupported operators/tools; untrusted prompt/tool data; authentication before real-data exposure.

## 13. Performance requirements
Bound retries and parallelism; account for all provider attempts, not only a final answer.

## 14. Dependencies on previous weeks
Week 01 concepts and existing provider/schema utilities.

## 15. Acceptance criteria
- **W02-AC01**: Valid requests return the declared JSON schema, with retries bounded and visible.
- **W02-AC02**: Malformed/model-invalid responses and unavailable provider paths fail with safe actionable errors.
- **W02-AC03**: The supported tool performs a real deterministic lookup/calculation in Python; unknown tools/invalid arguments are rejected.
- **W02-AC04**: Credentials are absent from committed files and error responses.
- **W02-AC05**: Any introduced React view completes the request/error flow against the same API contract.

## 16. Test scenarios and traceability
Reuse tests/test_tools.py, test_course.py and test_answer_quality.py; add targeted provider failure/validation cases only when behavior changes; React component/API tests when UI is implemented.

- W02-AC01 -> planned W02-V01: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.
- W02-AC02 -> planned W02-V02: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.
- W02-AC03 -> planned W02-V03: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.
- W02-AC04 -> planned W02-V04: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.
- W02-AC05 -> planned W02-V05: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.

Reusable source/evidence: app/ollama_client.py, app/tools.py, app/models.py; tests/test_tools.py and tests/test_course.py.

Current status: **Core local capabilities exist; React and production identity controls pending.** See [cross-week traceability](../docs/architecture/traceability.md). A generic test-suite pass does not replace acceptance evidence.

## 17. Out-of-scope items
An autonomous multi-step agent, vector storage and unnecessary orchestration libraries.

## 18. Risks and assumptions
Existing tests prove local fixtures and contracts, not production access controls; model retries can still exhaust.

Amend approved scope using [change control](README.md).
