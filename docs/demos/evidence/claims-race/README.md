# Claims race evidence index

All cases use the assistant-authored fictional claims in `course/insurance/triage-claims.json`; the local model is `llama3.2:3b`. Costs are reference estimates, not an Ollama invoice. No real claimant data or human labels are present.

| Directory | State | Use |
|---|---|---|
| `baseline/` | Partial older attempt | Preserve for provenance; do not use in aggregate comparisons. |
| `baseline-r2/` | Partial stopped attempt | Preserve; invalid enum behavior was observed. |
| `baseline-r3/` | Partial attempt interrupted after failures | Preserve; not a complete ten-case run. |
| `baseline-r4/` | Complete ten-case baseline with `summary.json` and `budget-stop.json` | Week 07 baseline and Week 08 comparison source. Agent top failure: invalid arguments in 10/10 cases. |
| `mitigation-r4/` | Complete ten-case one-prompt mitigation and before/after comparison | Invalid-argument mode decreased 10 -> 2; repeated calls appeared 0 -> 8; path pass stayed 0%. Five outcome-pass/path-fail traces are named in the summary. |

The API/React benchmark reader exposes only exact `baseline`/`mitigation` directories and versioned `*-rN` directories containing a completed `summary.json`; it rejects arbitrary path names. Never overwrite a partial or completed attempt. See the [Week 07](../../week-07-demo.md) and [Week 08](../../week-08-demo.md) guides.
