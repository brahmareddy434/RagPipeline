---
name: requirements-analysis
description: Analyze a requested week in this claims RAG repository, preserve approved requirements, and map acceptance criteria to existing code and verification.
---

# Requirements analysis

Read root AGENTS.md, requirements/README.md, the requested and previous weekly specs, and docs/architecture/{repository-audit,target-architecture,traceability,migration-roadmap}.md before scoping work. Inspect actual source; do not infer feature completion from a syllabus or filename.

The repository already implements HR coursework and local fictional claims MCP. Keep those distinct: HR scores do not satisfy claims Task D. Week 01 is theory-only; the initial explicit implementation gate is "Implement Week 01". Do not broaden a weekly request into all nine weeks or an unrequested architecture rewrite.

For each requested criterion, record existing capability, missing behavior, backend/UI/API/data impacts, security/performance implications, prerequisite inputs, stable Wxx-ACnn ID and concrete verification target. Each weekly spec must contain the 18 sections used in requirements/week-01.md. Use "not applicable" with a reason instead of inventing a database or UI requirement.

Critical unknowns block only dependent work: real-provider identity/auth, tenant model, authorized claims data and ambiguous coverage rules cannot be invented. Continue independent analysis. A fictional fixture must be labelled as such.

Preserve human work: random trace provenance, open coding, blind labels, predictions and wire annotations cannot be fabricated as personally completed. Record missing inputs honestly.

After approval, add a dated amendment explaining impacted IDs and contracts; do not silently rewrite approved specs. Produce a bounded implementation scope and update the traceability matrix with actual files/tests or explicitly planned checks.
