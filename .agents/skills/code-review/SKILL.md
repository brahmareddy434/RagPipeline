---
name: code-review
description: Review a scoped change in this repository for architecture, security and regressions, classify findings, and distinguish source review from executed verification.
---

# Code review

Read the requested week's acceptance IDs, relevant prior behavior, full staged/unstaged diff and docs/architecture/repository-audit.md. Conduct a separate reviewer pass after implementation. Do not label self-review as an independent external review; use another reviewer only when available and authorized.

For each finding provide Critical/High/Medium/Low/Informational severity, path/location, concrete failure trigger, impact and required correction. Inspect interfaces and actual behavior rather than counting folders/classes.

Check: domain boundaries and dependencies; duplication; safe exceptions and resource cleanup; API compatibility; authenticated tenant scope across query/source/memory; deletion permissions; pre-write redaction; private static assets; bounded uploads/provider calls; full agent budgets and costs; citation resolution; prompt injection and MCP trust boundary; frontend states, accessibility and token handling; migration and backup safety.

Mandatory regression comparison: current APIs and existing HTML screens, root CLI commands, Chroma collections, fixtures, HR workflows, MCP discovery, reviewed evidence/label hashes, and tests. A changed path or contract requires an explicit migration/compatibility decision. Verify any claimed removal is authorized and documented.

Inspect graded experiments for confounding changes, invented real traces, post-hoc labels, invalid before/after baselines and incorrectly counted cached tool calls. Real claims authentication and peer-agent evidence must remain pending when unavailable.

Fix Critical/High issues introduced in the change before completion. Pre-existing unresolved High risks must remain release blockers; do not certify production readiness because unit tests pass. Re-run affected checks after fixes. End with findings, corrections, actual validation evidence, residual risk and approve/changes-required status for the scoped change.
