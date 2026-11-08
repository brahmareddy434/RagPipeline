# Week 10 claims squad race (provisional cohort)

Cases: C01, C02, C03, C04, C05, C06, C07, C08, C09, C10

WARNING: the required Week-6 claims question cohort is absent from this repository. This run uses the existing ten Week-7/8 trajectory fixtures and is not a rubric-complete Week-6 comparison.

| Metric | Single agent | Manager + specialists |
|---|---:|---:|
| Pass rate (deterministic outcome proxy) | 0% | 90% |
| p50 latency | 48157 ms | 18871 ms |
| p99 latency | 70102 ms | 31118 ms |
| Total tokens | 54284 | 6780 |
| Mean cost per claim (estimated) | $0.001239 | $0.000207 |

Model: `llama3.2:3b`; server-owned paired budget: `{'max_steps': 6, 'max_seconds': 300.0, 'max_tokens': 64000, 'max_cost_usd': 0.08, 'max_tool_errors': 3, 'max_repeats': 2, 'scratchpad_chars': 6000}`.
Cost is the app's reference token estimate, not a provider invoice. Order: Alternated single-first/team-first by paired case to reduce fixed order bias. Judge: `course.claims_trajectories.assess` unchanged for both arms.
Context re-send multiplier: **0.1x**; dominant hand-off `manager->coverage_worker` = 53.2% of team tokens.
