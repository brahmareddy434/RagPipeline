# CI rollout plan

No executable workflow is enabled in this initial design pass. Backend packaging and the future React lockfile must be stable first.

Planned PR checks: pinned Python install, backend regression suite with real local MCP fixture servers, frontend install/build/component checks once present, API compatibility fixtures, secret/dependency scan, and retained sanitized failure reports. Live Ollama evaluation must be an explicit job with a configured runner and model; an unavailable provider cannot be reported as a passing evaluation.

Use least-privilege workflow permissions; no cloud publish, secrets export or deployment on untrusted pull requests. Add deployment jobs only after environment and release authorization are defined. Do not invent a working pipeline based on this plan.
