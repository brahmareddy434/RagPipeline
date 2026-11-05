# Week 06 - claims assertions and a gated judge

Objective: deterministic claims evaluation and an honest human-first judge workflow. W06-AC03-05 cannot complete without real blind labels/prediction; W06-AC01 still needs two verbatim real failure regressions.

## Start and show
Use the Week 03 application commands; open `/#/evaluation`. The screen shows six modes, counts, percentages and individual failed assertions. It explicitly distinguishes deterministic passes from the pending judge.

From root:
```powershell
.\.venv\Scripts\python.exe -m course.claims_evaluation assertions
# Only after a human independently labels E01-E25 with booleans:
.\.venv\Scripts\python.exe -m course.claims_evaluation seal path/to/human-labels.json path/to/sealed.json
# Commit sealed.json, then use a new output path:
.\.venv\Scripts\python.exe -m course.claims_evaluation judge path/to/sealed.json path/to/judge-v1.json
# After inspecting actual disagreements and committing a human prediction:
.\.venv\Scripts\python.exe -m course.claims_evaluation judge path/to/sealed.json path/to/judge-v2.json --previous path/to/judge-v1.json --prediction path/to/prediction.txt
```
The v2 path refuses fewer than two actual v1 disagreements, changed labels or uncommitted predictions. It embeds two real disagreements as examples. The same sealed 25 labels determine both agreement percentages. Judge calls are never run here with assistant-invented human labels.

## Implementation and evidence
`domain/claims.py` defines typed summaries/status. `services/claims_evaluation.py` supplies 30 explicitly synthetic cases and four assertions: claim-ID format, real calendar date, finite nonnegative numeric deductible and existence of a denial clause. A fifth concern, preserving uncertainty rather than inferring approval from progress, is the sole binary judge criterion. Deterministic fields are absent from both prompts and judge inputs. `course/claims_evaluation.py` hashes cases/labels, verifies committed seals, writes an exclusive pre-call receipt and retains complete model usage. `/claims/evaluation` returns only the fictional assertion report; it never exposes private labels. No database migration or new library.

Executed: 11 evaluation/trace tests passed; five frontend tests/build passed. The one-command 30-case report is `docs/demos/evidence/claims-evaluation/assertions.json`: valid and coverage-overclaim cases pass assertions; four intentionally malformed modes fail. Overclaim passing assertions demonstrates why semantic judgment is separate. No human agreement or measured v2 improvement is claimed. Optional RAGAS not run. Self-review checked date/boolean/NaN edge cases, clause reality, seal mutation and pre-judge ordering; human authorship still needs attestation.

Talk track: Check mechanical rules in code, grade one remaining semantic concern, and validate that judge against labels made before seeing its verdicts.
