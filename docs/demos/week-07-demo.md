# Week 07: claims agent and fixed workflow

This demo compares a hand-written bounded claims agent with a fixed record -> notes -> referenced policy clause -> summary workflow. Both use the same read-only tools, fictional ten-claim fixture, local model, answer schema and provider budget. It does not make a coverage decision.

## Run

From the repository root, with Ollama running and the configured model available:

```powershell
.\.venv\Scripts\python.exe -m course.claims_race docs/demos/evidence/claims-race/<new-baseline-directory>
```

The output directory must be new. Do not overwrite partial attempts. Each case records the full run and deterministic outcome/path assessment; `summary.json` reports latency p50, tokens, cost estimates, pass rates, path gap, argument validity, tool choice and step efficiency. `budget-stop.json` records the separate low-budget termination. Cost is a reference estimate, not an Ollama invoice.

Use the React **Agent and fixed workflow** screen for one interactive claim; use **Trajectory benchmarks** to inspect completed benchmark artifacts. The race runs sequentially to avoid local-model contention.

## Evidence and boundary

The checked-in dataset contains ten assistant-authored fictional claims. Required clause IDs appear in the fictional adjuster notes. No real claim records, human adjuster questions or human acceptance labels are included. The completed [baseline-r4 artifact](evidence/claims-race/baseline-r4/summary.json) shows agent outcome/path pass 0/0 vs fixed workflow 0.50/1.00. Agent p50 was 47.7 s and 54,264 tokens; fixed workflow p50 was 33.3 s and 19,054 tokens. The agent's top mode was invalid arguments in all ten cases. See the requirements amendment for costs, quality dimensions and the under-150-word verdict.

The separate `budget-stop.json` ends before provider invocation at a 500-token ceiling: `token_budget`, abstained, zero provider calls/tokens and complete usage accounting. The hard boundary is also covered by budget-specific unit tests.

The optional W07-AC06 long-note/lost-detail and cross-process memory experiment is not part of this run; the existing HR memory demo remains HR evidence and is not relabeled as claims evidence.
