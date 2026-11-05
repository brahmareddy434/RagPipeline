# Requirements → implementation → verification

Status is for the supplied insurance Task D scope. New specs are draft; module existence alone does not satisfy acceptance.

| Requirement group | Existing reusable source / evidence | Current status |
|---|---|---|
| [W01](../../requirements/week-01.md#15-acceptance-criteria) | course/guides/01_language_models.md; course/labs/foundations.py (optional existing experiments). | Learning material exists; current learner observations and mentor review pending. |
| [W02](../../requirements/week-02.md#15-acceptance-criteria) | app/ollama_client.py, app/tools.py, app/models.py; tests/test_tools.py and tests/test_course.py. | Core local capabilities exist; React and production identity controls pending. |
| [W03](../../requirements/week-03.md#15-acceptance-criteria) | app/document_loader.py, chunker.py, vector_store.py, retrieval.py, services.py; existing document/ask browser screen. | Working local RAG exists; insurance corpus, tenancy and production file lifecycle pending. |
| [W04](../../requirements/week-04.md#15-acceptance-criteria) | app/retrieval.py (BM25/RRF/rerank options), /inspect and /evaluate, course/run.py. Existing evidence is largely HR. | Mechanisms exist; required 12-question claims experiment not established. |
| [W05](../../requirements/week-05.md#15-acceptance-criteria) | app/trace_logger.py, evaluation/collect_week5_traces.py, course/review_notes.py, tests/test_trace_logger.py. | Trace/sampling building blocks exist; pre-write privacy, complete claims replay and authentic human analysis pending. |
| [W06](../../requirements/week-06.md#15-acceptance-criteria) | evaluation/week6/*, app/week6_assertions.py, tests/test_week6_week7.py; domain is HR. | Reusable evaluator pattern exists; Task D data, assertions and judge-validation evidence pending. |
| [W07](../../requirements/week-07.md#15-acceptance-criteria) | app/agent.py, agent_tools.py, workflow.py, memory.py, course/race.py, tests/test_agent.py. | Core orchestration exists; comparable ten-claim race and strict production budgets pending. |
| [W08](../../requirements/week-08.md#15-acceptance-criteria) | course/trajectory_eval.py, course/week8_questions.json, docs/KT_Week8_Failure_Modes_and_Trajectory_Evals.md. | HR trajectory evidence exists; Task D ten-claim results pending. |
| [W09](../../requirements/week-09.md#15-acceptance-criteria) | app/mcp_registry.py, app/week9.py, mcp_servers/*, config/mcp.*.json; evaluation/week9/submission. | Local Task D mechanics and evidence exist (2→4, zero diff); real platform/peer review/React/production isolation pending. |

## Execution records
When a week is requested, map each Wxx-ACnn to its actual test function, command, evidence file or human review. Record timestamp, environment, code/config hashes, dataset, expected/actual outcome and defect. Wxx-Vnn are planned acceptance checks, not executed tests.

Audit findings AUD-01 through AUD-12 track cross-week release risks. Resolve them in an authorized increment and rerun affected access-control/trace/API/UI checks. Authentic human grading, real-provider integration and frontend parity remain explicit gaps.
