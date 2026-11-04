# Week 5 Module 3: Evals and Error Analysis

## Deliverable

**Track:** C - HR policy

This deliverable reads 50 real requests from the current FastAPI RAG application. Each trace records the question, temperature, complete answer, confidence, citations, latency, UUID identifiers, and the retrieved evidence used by the application. The trace file is [week5_traces.json](week5_traces.json).

The application was not changed to alter its answer behavior. The only addition is a reproducible collector, [collect_week5_traces.py](collect_week5_traces.py), so the sample can be replayed and replaced with a fresh run.

## Why We Collected These Traces

A benchmark score alone cannot show whether this application retrieved the correct policy paragraph, abstained when evidence was absent, or produced an answer that was too broad. Reading the traces exposes those failure modes in the app's actual workflow.

The sample uses 50 unique questions across leave, conduct, safety, security, visitors, expenses, remote work, and out-of-scope controls. It varies generation temperature across `0.0`, `0.1`, `0.3`, `0.7`, `1.0`, and `1.5`. The questions were selected before reading the answers to reduce cherry-picking.

## How To Reproduce

From the repository root, start Ollama and FastAPI, then run:

```powershell
$python = "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe"
& $python evaluation/collect_week5_traces.py
```

This writes `evaluation/week5_traces.json`. The API must be running at `http://127.0.0.1:8000` and the configured Ollama chat and embedding models must be available.

## What A Complete Trace Contains

Each item in the JSON file contains:

- `trace_id`, `run_id`, `request_id`, `sequence`, and `collected_at`: UUID-based replay and audit identifiers.
- `question`, `category`, `expected_source`, `expected_answerable`, and `temperature`: test design and the input needed to repeat the request.
- `endpoint`, `request`, `http_status`, and `latency_ms`: request observability fields.
- `answer` and `confidence`: the application's output.
- `citations`: the chunks the application cited.
- `retrieved`: every returned chunk, including source, page, rank, score, retrieval method, chunk ID, and text.
- `status` and `error`: request failures are retained rather than silently discarded.

A reviewer can replay a trace with `POST /ask`, using its `request` object, then compare the new answer and evidence with the saved record. `X-Trace-ID` and `X-Request-ID` are sent as correlation headers for production-style collection, even though the current API does not yet echo them.

## Open-Coding Notes

Read each trace before assigning a group. Write one sentence that describes the observed problem, without explaining the cause too early. Use these checks:

| Check | Question |
|---|---|
| Retrieval | Is the best supporting policy chunk present and ranked highly enough? |
| Grounding | Does the answer stay within the retrieved evidence? |
| Abstention | Does the app say it does not know when the corpus lacks the answer? |
| Completeness | Does the answer include the important condition, exception, or contact? |
| Citation | Do citations support the answer and identify the relevant source? |
| Consistency | Would the same question likely receive the same answer at low temperature? |

Recommended note format:

`Trace week5-XX: [what the answer did]; [why that matters to a user].`

Do not write the group name in this first sentence. Grouping comes after all 20 notes are written.

## Initial Error Taxonomy

Use these plain-language groups after open coding. A trace can have one primary group and optional secondary groups.

| Group | Definition | Severity guide |
|---|---|---|
| Wrong or missing retrieval | The needed policy evidence is absent, weak, or outranked by unrelated text. | High when it causes a wrong policy answer. |
| Incomplete policy answer | Evidence is available, but the response omits a condition, exception, deadline, or responsible contact. | High for safety, leave, or compliance decisions. |
| Unsupported answer | The response asserts information not supported by the retrieved chunks. | High because it can mislead employees. |
| Correct abstention | The app correctly says the corpus does not establish an answer. | No defect; retain as a control outcome. |
| Citation or traceability issue | The answer may be useful, but the citation does not make the supporting evidence easy to verify. | Medium; high if the source is wrong. |
| No observed defect | Retrieval, answer, grounding, and citation are all adequate. | No defect; retain as a control outcome. |

## Ranking Method

Rank problem groups by **frequency x severity**. For each trace, assign:

- `frequency_count`: number of traces whose primary problem is this group.
- `frequency_rate`: `frequency_count / 20`.
- `severity`: 1 (cosmetic), 2 (minor), 3 (meaningful), 4 (high user impact), or 5 (safety/compliance risk).
- `priority_score`: `frequency_count x severity`.

Do not count correct abstentions or no-defect controls as errors. Report them separately so the error rate is not inflated.

### Ranked Results

The completed review below is based on the 20 traces in [week5_traces.json](week5_traces.json). The counts are primary labels, so each trace is counted once.

| Rank | Problem group | Count | Rate | Severity (1-5) | Priority score | Example trace IDs |
|---:|---|---:|---:|---:|---:|---|
| 1 | Source contains unresolved template placeholders | 3 | 15% | 4 | 12 | week5-04, week5-16, week5-17 |
| 2 | Evidence-backed question incorrectly abstained | 1 | 5% | 4 | 4 | week5-07 |
| 3 | Incomplete or over-broad answer | 1 | 5% | 3 | 3 | week5-10 |
| 4 | Correct abstention control | 2 | 10% | 0 | 0 | week5-19, week5-20 |
| 5 | No observed defect | 13 | 65% | 0 | 0 | week5-01, week5-02, week5-03, week5-05, week5-06, week5-08, week5-09, week5-11, week5-12, week5-13, week5-14, week5-15, week5-18 |

## Chosen Fix Target And Prediction

The next target is **source contains unresolved template placeholders**. It has the highest priority score and affects employee-facing policy precision. This is primarily a corpus-quality issue, not an embedding-algorithm issue.

> If we replace the handbook's unresolved bracketed values with approved HR policy values, then the placeholder-error count will fall from 3/20 to 0/20 and the answers for dress code, reimbursement, and remote-work limits will become specific, while the two out-of-scope questions will remain correctly abstained.

Suggested measurements:

- retrieval hit-rate@3 and MRR using the evaluation endpoint;
- number of unsupported answers in the 20 trace notes;
- number of incomplete policy answers;
- correct-abstention count for out-of-scope questions;
- citation source accuracy.

## Similar Algorithms And When To Use Them

The current retriever uses dense semantic search plus BM25 keyword search and combines ranks with Reciprocal Rank Fusion (RRF). Alternatives are useful for diagnosis, but should be compared one at a time:

| Approach | Strength | Trade-off |
|---|---|---|
| Dense vector search | Finds paraphrases and related meaning. | Can miss exact policy terms, IDs, and deadlines. |
| BM25 | Strong for exact words, policy names, and codes. | Weak when the user paraphrases the policy. |
| Hybrid RRF (current) | Combines semantic and exact-match strengths without score calibration. | Adds tuning and can still rank an irrelevant long chunk highly. |
| Cross-encoder reranking | Re-scores a small candidate set using question-context interaction. | More latency and local compute. |
| Maximal Marginal Relevance | Reduces duplicate chunks and increases evidence diversity. | May remove useful overlapping context if diversity is over-weighted. |
| Query expansion or rewriting | Adds alternate terms such as PTO and paid time off. | Can introduce terms that change the user's intent. |
| Parent-child retrieval | Retrieves a precise child chunk, then supplies its larger parent section. | Requires parent metadata and more storage. |
| BM25 plus metadata filters | Restricts search by document type, team, or policy area. | Requires reliable metadata and a known filter value. |

For this small HR corpus, start with retrieval evidence and error counts before adding a larger model or a more complex retriever.

## Benchmarks Versus This Application

MMLU and HumanEval are broad external benchmarks. MMLU measures knowledge-question performance across subjects; HumanEval measures code-generation correctness. They are useful for comparing models under standardized conditions, but they do not measure whether this application retrieved the right company policy or cited it correctly.

This app needs a task-specific benchmark: fixed HR questions, expected source names, retrieval hit-rate@k, MRR, grounded-answer review, and correct abstention. Keep the 20 trace questions as a regression set after the first fix.

## Inputs For Mentor Evaluation

Share these items with the mentor:

1. `evaluation/week5_traces.json` - the 20 complete traces.
2. `evaluation/week5_error_analysis.md` - this report and the review method.
3. The exact collection command:

```powershell
$python = "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe"
& $python evaluation/collect_week5_traces.py
```

4. The API replay input for any trace:

```json
{
  "question": "<copy question from the trace>",
  "temperature": 0.1
}
```

Send it to `POST http://127.0.0.1:8000/ask`.

5. The mentor's review checklist:

- Did the sample contain 50 real requests selected before reading answers?
- Is there one honest open-coded sentence per trace?
- Are the groups named clearly enough for a stranger to understand?
- Are correct abstentions and no-defect controls separated from failures?
- Are groups ranked by frequency and severity?
- Is one next fix selected with a measurable prediction?
- Are the complete trace file and replay input included?

## Mentor Review Notes

| Trace ID | One-sentence open code | Primary group | Severity (1-5) | Evidence for judgment |
|---|---|---|---:|---|
| week5-01 | The answer gives the 20-day annual leave rule and cites the leave policy. | No observed defect | 0 | Evidence supports the answer. |
| week5-02 | The answer gives the five-working-day notice rule for planned leave. | No observed defect | 0 | Evidence supports the answer. |
| week5-03 | The answer gives the same-day emergency leave process and manager notification. | No observed defect | 0 | Evidence supports the answer. |
| week5-04 | The answer repeats unresolved alternatives such as Business or Casual instead of a single policy value. | Source contains unresolved template placeholders | 4 | Bracketed alternatives appear in the retrieved handbook text. |
| week5-05 | The answer correctly allows limited personal email use and includes safety conditions. | No observed defect | 0 | Answer is grounded in the retrieved handbook. |
| week5-06 | The answer directs the employee to Security Specialists for a suspicious message. | No observed defect | 0 | Answer is grounded in the retrieved handbook. |
| week5-07 | The answer abstains even though retrieved handbook evidence describes phone use while driving. | Evidence-backed question incorrectly abstained | 4 | Relevant evidence was retrieved but not used. |
| week5-08 | The answer explains the smoke-free workplace rule and restrictions. | No observed defect | 0 | Answer is grounded in the retrieved handbook. |
| week5-09 | The answer gives the shredding requirement for confidential documents. | No observed defect | 0 | Answer is grounded in the retrieved handbook. |
| week5-10 | The response lists several possible contacts and includes unnecessary or confusing guidance. | Incomplete or over-broad answer | 3 | The answer is broader than the direct contact question. |
| week5-11 | The answer directs witnesses of severe violence to building security. | No observed defect | 0 | Answer matches the retrieved safety guidance. |
| week5-12 | The answer correctly states the manager-dating restriction. | No observed defect | 0 | Answer is grounded in the retrieved handbook. |
| week5-13 | The answer includes visitor permission, identification, sign-in, and supervision requirements. | No observed defect | 0 | Answer is grounded in the retrieved handbook. |
| week5-14 | The answer distinguishes overtime pay from the missing maximum-hours rule. | No observed defect | 0 | The response states the limit is not specified. |
| week5-15 | The answer gives the three-month expense-submission deadline. | No observed defect | 0 | Answer is grounded in the retrieved handbook. |
| week5-16 | The answer exposes unresolved placeholders for reimbursement timing and payment method. | Source contains unresolved template placeholders | 4 | Bracketed values appear in the retrieved handbook text. |
| week5-17 | The answer confirms remote work but repeats unresolved bracketed limits and conditions. | Source contains unresolved template placeholders | 4 | Bracketed values appear in the retrieved handbook text. |
| week5-18 | The answer includes the local-law caveat for accrued PTO at separation. | No observed defect | 0 | Answer preserves the important qualification. |
| week5-19 | The app correctly says the handbook does not establish gym-membership coverage. | Correct abstention control | 0 | No supporting policy was available. |
| week5-20 | The app correctly says the handbook does not establish an office-parking fee. | Correct abstention control | 0 | No supporting policy was available. |
