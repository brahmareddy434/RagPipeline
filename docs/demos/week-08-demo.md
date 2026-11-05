# Week 08: claims trajectory evaluation

The evaluator separates answer outcome from the path used to reach it. Expected paths are generated from the fictional fixture before a run; arguments are validated against the real repository IDs, not only a regular expression. The report includes valid tool choices, argument validity, step efficiency, latency and cost p50/max, failure modes, and right-answer/wrong-path cases.

## Run and inspect

The completed [baseline-r4](evidence/claims-race/baseline-r4/summary.json) measured invalid arguments in all ten agent cases. The completed [mitigation-r4 comparison](evidence/claims-race/mitigation-r4/comparison.json) shows invalid arguments falling 10 to 2 and outcomes rising 0% to 50%; repeated calls rose 0 to 8, path pass stayed at 0%, and p50 latency rose by 27.1 seconds. The mitigation improved answer proxy checks but did not produce an accepted trajectory. Five actual outcome-pass/path-fail traces are C04, C06, C07, C09 and C10. No second mitigation was added.

```powershell
.\.venv\Scripts\python.exe -m course.claims_race docs/demos/evidence/claims-race/mitigation-r4 --baseline docs/demos/evidence/claims-race/baseline-r4
```

The runner checks that model, budgets and frozen source hashes match, and allows the prompt change only when missing-clause behavior is the measured top baseline mode. Review `comparison.json` for per-mode deltas and numeric price, and the React Trajectory benchmarks view for the same artifacts.

## Evidence boundary

These are deterministic proxies over assistant-authored fictional claims using one installed local model. They are not human labels, real claimant cases or proof of general prompt-injection robustness. Failed and partial attempts remain preserved as evidence; create a new directory for each rerun.
