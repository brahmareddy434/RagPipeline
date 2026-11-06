# CI rollout plan

`validate.yml` now runs Python regression tests (including local MCP fixture processes), React build and component tests on push/PR with read-only repository permissions. It has not been executed on GitHub in this local session. Python dependencies retain the repository's existing ranges; a portable lock remains a release improvement. Frontend uses its committed lockfile. Live Ollama/Edge journeys run explicitly on a configured local machine.

Planned PR checks: pinned Python install, backend regression suite with real local MCP fixture servers, frontend install/build/component checks once present, API compatibility fixtures, secret/dependency scan, and retained sanitized failure reports. Live Ollama evaluation must be an explicit job with a configured runner and model; an unavailable provider cannot be reported as a passing evaluation.

Use least-privilege workflow permissions; no cloud publish, secrets export or deployment on untrusted pull requests. Add deployment jobs only after environment and release authorization are defined. Do not invent a working pipeline based on this plan.
