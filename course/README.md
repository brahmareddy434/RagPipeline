# Seven week AI engineering course

Start with [the readable course index](index.html). Each week has a detailed Markdown guide and a standalone HTML reading copy.

## Quick start

Run commands from C:\AI Practice\ollama-rag-fastapi.

~~~powershell
# Terminal one
.\start_course.ps1

# Terminal two
.\.venv\Scripts\python.exe -m course.run seed
.\run_evals.ps1
~~~

Open http://127.0.0.1:8001 for the inspection screen or http://127.0.0.1:8001/docs for Swagger.

If you are switching to a different document set, click **Clear indexed documents** first. The same reset is available from PowerShell:

~~~powershell
Invoke-RestMethod http://127.0.0.1:8001/documents -Method Delete
~~~

Then upload the documents you want to query. This prevents an older document from supplying conflicting policy text.

The course uses a separate course_hr_v2 collection. The historical knowledge_base collection and evaluation files remain available. Course policies are fictional training examples, not approved real HR decisions.

## Week by week

| Week | Read | Run or demonstrate | Evidence |
|---|---|---|---|
| 1 | [Language models](guides/01_language_models.html) | No coding required; explain tokens, costs and hallucination | Your own explanation and observation notes |
| 2 | [Prompting and tools](guides/02_prompting_and_tools.html) | /tools/run and /tools/parallel | Safe tool output and broken-input tests |
| 3 | [RAG](guides/03_retrieval_and_rag.html) | python -m course.run week3 | results/week3_retrieval.json |
| 4 | [Retrieval debugging](guides/04_debugging_retrieval.html) | python -m course.run week4 | results/week4_retrieval.json |
| 5 | [Trace analysis](guides/05_trace_analysis.html) | python -m course.run week5 | Blank sample plus separate assistant review |
| 6 | [Evaluations](guides/06_evaluations_and_judges.html) | .\run_evals.ps1 -Live -Judge | Fresh paired outputs and judge calibration |

Use .\.venv\Scripts\python.exe wherever the table abbreviates python.

## What to show your mentor

1. Health, a supported answer and a source link.
2. An unknown answer and a safe calculator rejection.
3. Two chunk sizes with measured results, including a tie if neither improved.
4. One retrieval change and before/after ranks.
5. Your own notes on a seeded sample, a ranked taxonomy, and a prediction.
6. A live evaluation report and an honest judge-validation decision.
7. An agent run with every step visible, a budget stopping it safely, and the race numbers against the fixed workflow.

## Scope

The core app is local, single-user coursework. It does not provide tenant authorization, malware scanning, OCR, immutable document history, a background ingestion queue, or a production deployment. Optional libraries and paid-provider examples are identified in the coverage and validation documents.

A prepared worksheet is not your human grading. A rejected judge is not a validated judge. A measured training-set gain is not a guarantee about unseen questions.

## Regenerate reading copies

~~~powershell
.\.venv\Scripts\python.exe -m course.build_guides
~~~
