# Curriculum coverage and implementation map

This map distinguishes implemented core behavior, optional integration exercises, and theory. Week 1 is intentionally theory-only. The curriculum names alternatives; it does not require three vector databases or every paid provider to run in the core application.

| Week | Topics | Location and evidence |
|---|---|---|
| 1 | Language models; tokens and tokenization; cost per token; context window; hallucination | Guide 1 sections 1–3 and 7–8; optional foundations usage/cost lab |
| 1 | Word2Vec; GloVe; static versus contextual embeddings | Guide 1 section 5; conceptual study, not a claim of training these models |
| 1 | Temperature; top-p; top-k; greedy versus sampled decoding | Guide 1 section 4; foundations sampling and temperature demos |
| 1 | GPT, Claude and Llama families; encoder versus decoder; model choice | Guide 1 sections 6 and 8 |
| 2 | Prompt anatomy; zero-shot and few-shot | Guide 2 section 2; app/prompts.py worked example |
| 2 | CoT; self-consistency; task decomposition | Guide 2 sections 3–4; explicit stages, evidence explanations rather than hidden reasoning |
| 2 | JSON schema; Pydantic; validation and retry | app/models.py and app/ollama_client.py; tests/test_course.py |
| 2 | instructor | Optional real integration in course/labs/optional_integrations.py; extra dependency |
| 2 | Tool/function calling; parallel calls | app/tools.py; /tools/run and /tools/parallel; Python executes |
| 2 | Guardrails; prompt injection; secret handling | Bounded calculator, strict arguments, evidence validation, fictional injection case, environment-only optional keys |
| 3 | Why RAG; bi-encoder versus cross-encoder | Guide 3 sections 1 and 5 |
| 3 | Chunking strategies; size and overlap | app/chunker.py; measured course.run week3 |
| 3 | Dense retrieval; MTEB; BGE; E5 | Ollama embeddings in core; guide comparison and model-specific prefix explanation |
| 3 | Vector databases; HNSW; Qdrant/Chroma/pgvector | Chroma implemented; alternatives explained in Guide 3 |
| 3 | Similarity search; top-K; metadata filtering | app/vector_store.py and RetrievalOptions; filename filter |
| 3 | Grounding; citations; unknowns | Structured claims with quote membership and source-excerpt links |
| 4 | Retrieval versus generation failures; inspection view | /inspect and browser screen; historical failure examples |
| 4 | Keyword versus semantic; BM25; RRF | app/retrieval.py; measured course.run week4 |
| 4 | Cross-encoder; BGE-Reranker; Cohere Rerank | Optional cross-encoder adapter and external-provider lab; Guide 4 |
| 4 | MMR | Implemented vector-based relevance/diversity selection |
| 4 | Query rewriting; HyDE | Implemented opt-in transformations; transformed query visible; hypothetical text never evidence |
| 4 | Hit-rate@k; recall@k; MRR | /evaluate and course experiments; source-level unit stated |
| 5 | Complete traces; random versus curated | /ask traces plus seeded sample with population fingerprint |
| 5 | Open coding; taxonomy; frequency × severity | Separate blank worksheet and assistant notes; rank command |
| 5 | Fix target; prediction first; MMLU/HumanEval versus app | Guide 5; live experiment records prediction before generation |
| 6 | Eval sets; regressions from failures; assertions | course/eval_set.json; offline tests; live runner |
| 6 | LLM-as-judge; binary versus numeric; human agreement | Real Ollama judge and confusion-class agreement gate; imported-label provenance |
| 6 | G-Eval | Explained as a distinct research method; no false claim of full reproduction |
| 6 | RAGAS faithfulness/relevancy/context precision/recall | Guide definitions; optional library faithfulness demo; custom proxy clearly labelled |
| 6 | Before/after per-type deltas | course/results/week6_live.json; actual outputs, not authored candidate answers |
| 7 | The agent loop; ReAct | app/agent.py; one hand-written while loop, thought/action/observation recorded per step |
| 7 | Tool design | app/agent_tools.py; four tools, Pydantic-validated arguments, descriptions that state what each tool cannot do |
| 7 | Stop conditions and budgets | AgentBudget: steps, wall clock, tokens, tool errors, repeated calls; a bounded stop still answers and reports stop_reason |
| 7 | Workflows versus agents | app/workflow.py; three hard-coded stages, one generation call, with its structural blind spot documented |
| 7 | Agent versus workflow race | course/race.py over course/week7_scenarios.json; speed, cost and reliability with pass conditions declared before the run |
| 7 | Agent memory, short and long term | app/memory.py; Scratchpad for in-run context, VectorMemory for cross-run facts scoped per session |
| 7 | Summarisation and vector memory | Scratchpad.compress folds old steps into notes; VectorMemory embeds and recalls by meaning |
| 7 | mem0 | Explained as the hosted equivalent of VectorMemory in Guide 7; not installed or invoked |
| 7 | LangChain / LangGraph | Guide 7 section 8 maps the hand-written loop onto AgentExecutor and a state graph; neither is a dependency |
| 8 | Agent failure modes; trajectory evaluation | course/trajectory_eval.py over course/week8_questions.json; ten HR cases with pre-declared expected tool sequences, run against the live agent |
| 8 | Expected tool sequences; tool-choice accuracy | Each question declares required/optional/forbidden tools and the correct first tool; alternate legitimate paths (e.g. an optional jurisdiction check) are accepted, not over-asserted |
| 8 | Outcome vs trajectory gap | course/results/week8_trajectory_before.json: outcome pass rate 50%, trajectory pass rate 20%, gap +30%; a named right-answer/wrong-path case (q01) and its recorded tool sequence |
| 8 | Cost per task (mean & p99 asked for; p50 & max reported here) | Reported as p50 and max, not mean, per question set; course/results/week8_trajectory_before.json and _after.json |
| 8 | Fixing the worst failure and measuring it went down | Mitigation: AgentBudget.max_steps default 6 to 4 (app/models.py), targeting the top failure mode ("loop", 10/10 questions before to 3/10 after); price paid measured as a 20-point outcome pass-rate drop, root-caused per question in docs/KT_Week8_Failure_Modes_and_Trajectory_Evals.md, not claimed free |
| 8 | Indirect prompt injection | course/data/employees.json EMP-1004.manager_comment; undefended attack in course/results/week8_trajectory_attack_before.json makes the agent state an "unlimited (999 days)" balance and recommend auto-approval |
| 8 | Tool sandboxing & least privilege; output validation | app/agent_tools.py sanitize_free_text (strips instruction-like sentences from a tool result before it becomes evidence) plus app/answer_quality.py flag_injected_language (a second-layer check on the drafted answer, wired into app/agent.py's existing retry path); re-attack in course/results/week8_trajectory_attack_after.json fails to leak the injected claim |
| 8 | OWASP LLM Top 10 | Demonstrates LLM01 (prompt injection, indirect) and touches LLM07 (insecure plugin/tool design) via the read-only, single-purpose tool scoping already in place from Week 7 |

## Week 7 honesty notes

The race measures this corpus, these eight scenarios and this local model. A different model changes the numbers more than any prompt edit here does. mem0, LangChain and LangGraph are explained and mapped onto the hand-written equivalents rather than installed, because the point of the week is that the loop is not magic. The memory demonstration reports its own result: if the warm run does not take fewer steps, that is what the output says.

## Human work that cannot be supplied on your behalf

Read and grade the twenty traces yourself, confirm imported calibration labels, explain the code in your own words, and discuss the tradeoffs with your mentor. The assistant review is a worked example, not proof that you performed those learning tasks.

## Core versus advanced setup

Core dependencies are in requirements.txt. Optional examples use requirements-optional.txt. Cross-encoder models need a separate model download. Cohere needs a user-provided key and incurs provider usage; it is not silently invoked. The exact checks completed are recorded in the per-week KT documents under docs/.
