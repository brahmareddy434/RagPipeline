---
name: testing
description: Plan and execute relevant backend, React, API, RAG and agent regression checks for a requested change, recording actual outcomes and provider limitations.
---

# Testing

Read AGENTS.md, the weekly acceptance IDs, changed contracts and the existing tests before writing new ones. Select checks based on changed behavior and concrete risks; avoid tests that merely mirror implementation or assert documentation wording.

Current backend command: .venv/Scripts/python.exe -m pytest -q from the repository root. MCP integration tests launch real local stdio/HTTP fixture servers and may require Windows subprocess permissions. Apply approved scoped escalation rather than replacing them with mocks and claiming the same coverage.

Cover the changed layer: pure unit behavior, service/repository contracts, API inputs/status/errors, real disposable storage, identity/tenant denial, provider timeouts and resource cleanup. Preserve earlier test cases and use isolated temporary data; never clear the user's live Chroma collection to test.

RAG checks include ingestion limits/parser failure, chunk boundary metadata, retrieval known IDs/editions, context bounds, grounded citations/abstention and malicious document text. Agent checks include invalid real IDs, allowed alternative paths, repeats, budget termination across all model phases, and summed usage. Distinguish deterministic tests from stochastic live model evaluation.

When React exists, verify components/forms/hooks, API states, routing/accessibility and complete upload/ask/source/run journeys in a browser. No frontend test result exists before a runnable frontend is built.

For each acceptance ID record command/test function, fixture provenance, expected vs actual result, timestamp/environment, status and defects. Live integration checks need an available authorized provider; state exactly what is mocked, local or real. A passing test does not supply human blind labels, handwritten observations or real third-party access.

After fixes run relevant regressions; once they pass do not repeatedly rerun unchanged suites. Report test counts and limitations only from tool output. Document explicit exceptions when approved removal makes an old regression inapplicable.
