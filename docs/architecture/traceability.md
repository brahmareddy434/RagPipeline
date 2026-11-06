# Requirements -> implementation -> verification

Status covers the supplied insurance Task D scope. On 2026-11-05 the user authorized Weeks 01-09 and the React frontend. This matrix distinguishes locally implemented work from human, real-data, peer and production acceptance inputs. A passing test suite does not replace those inputs.

| Week | Local implementation and evidence | Remaining acceptance boundary |
|---|---|---|
| [W01](../../requirements/week-01.md#15-acceptance-criteria) | Theory guide, local model/embedding experiments and dated evidence; [demo](../demos/week-01-demo.md). | Learner's own explanation and mentor review. |
| [W02](../../requirements/week-02.md#15-acceptance-criteria) | Modular backend, compatibility `app/`, structured tools and React workbench; access tests and demo. | Real identity provider and production deployment controls. |
| [W03](../../requirements/week-03.md#15-acceptance-criteria) | Claims upload, grounded ask, sources, retrieval inspection and React views; isolated browser evidence. | Real claims documents/provenance and multi-user production storage. |
| [W04](../../requirements/week-04.md#15-acceptance-criteria) | Frozen 12-question fictional retrieval experiment: semantic and RRF both 12/12; no gain claimed. | Authentic adjuster questions; optional MMR. |
| [W05](../../requirements/week-05.md#15-acceptance-criteria) | Pre-write redaction, fictional trace replay, synthetic sampler and React traces. | Human trace coding, authentic failure taxonomy and prediction. |
| [W06](../../requirements/week-06.md#15-acceptance-criteria) | Thirty synthetic cases, deterministic assertions, judge gates and React evaluation. | Real regressions, blind human labels/predictions and judge agreement. |
| [W07](../../requirements/week-07.md#15-acceptance-criteria) | Claims agent/fixed workflow, typed read-only tools, hard provider budgets, race runner and React comparison. | Final live local-model race results and verdict limited to fictional cases. |
| [W08](../../requirements/week-08.md#15-acceptance-criteria) | Expected paths, fixture ID validation, outcome/trajectory metrics and one measured prompt mitigation. | Baseline/mitigation local-model runs; no general robustness claim. |
| [W09](../../requirements/week-09.md#15-acceptance-criteria) | Claims MCP server/config, host discovery, React inventory/traces; existing wire/gateway evidence. | Actual claims platform, human annotation, peer call and production isolation. |

Audit findings AUD-01 through AUD-12 remain the release-risk index. Real identity, real claimant data, authentic human review, peer call and production deployment are not represented as complete.

## Execution records

2026-11-06 mentor-demo extension: Week 8 `/demo/week8` accepts typed queries with baseline/mitigation and isolated injection-note options; Week 9 `/demo/week9` compares live discovery and queries against the two allowlisted configurations. Both explain prior behavior, identified issue, change and observed result. Historical r4 scores and Week 9 snapshots remain unchanged. New service/route contracts are checked in `tests/test_mentor_demo.py`; interactive and cancellation flows in `frontend/e2e/mentor-demo.spec.ts`; local HTTP discovery/validation assertions in `docs/postman/Mentor_Demos.postman_collection.json`.

When a week is requested, map each Wxx-ACnn to its actual implementation and verification. Planned Wxx-Vnn checks are not executed tests. Dated commands, manifests and evidence are linked from weekly requirements and mentor demos. See [execution report](completion-report.md) for current test results and run limitations.

Week 01 execution (2026-11-05): assistant-run material and live observations recorded; learner explanation and mentor acceptance remain pending. Exact commands and outcomes are in requirements/week-01.md and its demo/evidence.
