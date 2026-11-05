# Week 01 - language model foundations

**Status (2026-11-05):** theory materials and assistant-run experiments complete; learner explanation and mentor sign-off pending. Scope: W01-AC01 to W01-AC05. No application programming is required this week.

## What we did and which files matter

We reused the existing learning guide and helpers, ran local experiments, and saved their outputs with model/version/configuration metadata. Backend, React, API, database, agent and RAG behavior are unchanged; no dependencies or services were added. The future backend/frontend migration remains separate work.

| File | Purpose / Week 01 change |
|---|---|
| `requirements/week-01.md` | Existing scope plus dated execution status and acceptance evidence |
| `docs/demos/week-01-demo.md` | This single startup, explanation and mentor walkthrough |
| `docs/demos/evidence/week-01-experiments.json` | New reviewed evidence: outputs, token counts, similarities, versions, hashes and validation |
| `course/guides/01_language_models.md` | Existing detailed theory reference; unchanged |
| `course/labs/foundations.py` | Existing sampling, cost, temperature and embedding helpers; unchanged |
| `app/ollama_client.py`, `app/config.py` | Existing provider wrapper/configuration reused by those helpers; unchanged |
| `docs/architecture/traceability.md`, `migration-roadmap.md` | Record Week 01 evidence and remaining learner review |
| Root, requirements, docs and demo README files | Update navigation/status; existing five reusable skills remain in use |

## Start the demonstration

For the recorded presentation, open this document and the evidence JSON in your editor: **no application startup is needed**. For a fresh experiment, use PowerShell from the repository root, the existing Python 3.11 virtual environment and local Ollama with `llama3.2:3b` and `nomic-embed-text:latest` already installed.

```powershell
Set-Location 'C:\AI Practice\ollama-rag-fastapi'
ollama list
# If Ollama is not already running, start it in another terminal:
ollama serve
```

Run `ollama serve` only when no service is running. The helpers read the existing `.env`; for these examples it selects `OLLAMA_BASE_URL=http://localhost:11434`, `OLLAMA_CHAT_MODEL=llama3.2:3b`, and `OLLAMA_EMBED_MODEL=nomic-embed-text:latest`. Keep `.env` private. No cloud key is needed. Missing model downloads are a setup prerequisite, not part of the recorded run.

**Backend/frontend startup:** not applicable to this theory demo. FastAPI and Chroma are not started or modified; no React project exists yet. Show the editor and terminal, with no new UI page or application API to test.

## Explain the concepts in plain words

| Concept | Short explanation to practise in your own words |
|---|---|
| Language model | Predicts a next token from the supplied context, appends it, and repeats. Training changes weights; ordinary inference uses learned weights. |
| Hallucination | Fluent text can contain unsupported facts. Illustrative example, not a measured result: saying a fictional policy definitely covers flooding without seeing its wording. Verify evidence or say the answer is unknown. |
| Tokens / context | Tokens are text pieces, not necessarily words. Context is the request's limited working space for instructions, history, evidence and output; a file on disk is not automatically in that space. |
| Sampling | Greedy decoding chooses the highest-scoring next token. Temperature changes the distribution; top-k limits candidates by count and top-p by cumulative probability. None adds missing facts. [Runtime parameters](https://docs.ollama.com/modelfile). |
| Embeddings | Vectors let us compare text meaning. Similarity is neither truth nor coverage approval. RAG retrieves evidence for the prompt; it does not retrain the model. |
| Static / contextual | Basic Word2Vec/GloVe word vectors use one representation per word; contextual representations can distinguish a river bank from a financial bank. [Word2Vec](https://arxiv.org/abs/1301.3781), [GloVe](https://nlp.stanford.edu/projects/glove/), [BERT](https://arxiv.org/abs/1810.04805). |
| Encoder / decoder | Encoders commonly build input representations; autoregressive decoders generate tokens. Encoder-decoder designs combine both. Embeddings are not restricted to encoder-only architectures. |
| Model choice | GPT, Claude and Llama are model families. Compare task quality, privacy, context needs, latency, memory and total cost. We reused the installed Llama model; we did not rank providers or claim current hosted prices. |
| Agent | Application code executes tools and manages the loop; the model proposes outputs/actions. An embedding model supplies vectors, not the final answer. |

## Actual experiment and cost calculation

Run on **2026-11-05**, Python 3.11.9, Ollama 0.40.14; chat `llama3.2:3b`, embeddings `nomic-embed-text:latest`. Exact model digests and helper hashes are in the JSON. These are assistant-executed observations, not learner-authored evidence.

Prompt: **Name a fictional bakery in three words.** Same prompt/model and `top_p=0.9`, `top_k=40`, `num_predict=60`; only temperature changes between groups. Seed and context size were not overridden. Request/response meaning follows the [Ollama chat reference](https://docs.ollama.com/api/chat).

| Run | Temperature | Actual answer (quotes preserved) | Input / output tokens | Server duration (s) |
|---|---:|---|---:|---:|
| 1 | 0 | `"Sweet Delight Bakery"` | 33 / 7 | 10.082 |
| 2 | 0 | `"Sweet Delight Bakery"` | 33 / 7 | 0.941 |
| 3 | 0.8 | `Mystic Sweet Delights` | 33 / 7 | 0.669 |
| 4 | 0.8 | `"Moonlit Sweet Delights"` | 33 / 8 | 0.834 |

**Observation:** 1 unique answer out of 2 at temperature 0; 2 out of 2 at 0.8. This tiny sample illustrates variation, not correctness or guaranteed determinism. The first call includes 8.998 seconds of model loading; these sequential, unseeded samples cannot establish a temperature speed advantage. Counts total **132 input + 29 output tokens** and include model message formatting, not just visible words. Durations are server nanoseconds converted to seconds, not end-to-end latency.

The three-text embedding batch returned **768 dimensions**. Cosine similarity of "Annual leave allowance" with "How much vacation do I receive?" was **0.5059**, versus **0.3220** with "A bicycle has two wheels." These existing generic examples are not insurance retrieval-quality evidence.

**Hypothetical USD prices, dated 2026-11-05:** $1 per million input tokens and $4 per million output tokens. `(2,000 x 1 + 500 x 4) / 1,000,000 = $0.004` per call; 1,000 calls = **$4**. At those same invented rates, this experiment's chat tokens would cost `(132 x 1 + 29 x 4) / 1,000,000 = $0.000248`, excluding embeddings and other fees. Actual local inference has no hosted token bill; hardware, electricity and time were not costed. These figures are not vendor quotes.

## Replicate and show your mentor (about five minutes)

1. Explain prediction, hallucination, tokens, context and embeddings using the table above. Use the unsupported flood-coverage example to distinguish fluent wording from evidence.
2. Run the existing numerical helpers. Expected: an explicitly invented four-token distribution that becomes flatter at higher temperatures, and `hypothetical_USD: 0.004`.
   ```powershell
   .\.venv\Scripts\python.exe -m course.labs.foundations sampling
   .\.venv\Scripts\python.exe -m course.labs.foundations cost
   ```
3. Run the existing live helpers. Expected: four records containing `temperature`, `answer`, and `actual_ollama_counts`; then texts, dimension count and a 3-by-3 similarity matrix. Names/counts/timings can differ on rerun.
   ```powershell
   .\.venv\Scripts\python.exe -m course.labs.foundations temperature
   .\.venv\Scripts\python.exe -m course.labs.foundations embeddings
   ```
4. Open `docs/demos/evidence/week-01-experiments.json`. Compare the fresh terminal output with the dated record; preserve the original. Show the prompt/options, model digests, outputs and counts. Explain why warm-up and randomness limit conclusions.
5. Work the $0.004 calculation aloud, then explain why local running costs still exist. Show `requirements/week-01.md` for criteria and pending learner review. Write your own explanation/observations and ask the mentor to assess them.

## Verification, decisions and limitations

Live checks executed: four chat responses and one embedding batch. Numerical helper checks and artifact/source-integrity validation are recorded under `verification` in the evidence JSON. Source preservation is checked against this turn's initial working-tree hashes, including prior uncommitted Week 9 work; comparing all changes to HEAD alone would conflate the two tasks.

Review is a separate **self-review**, not an external review. No new Critical/High issue was found in this documentation/evidence scope. The existing production blockers remain in [the repository audit](../architecture/repository-audit.md). No runtime contract, UI screen or persisted database changed, so API/UI/database regression tests and the full pytest suite were not rerun for this theory-only change. The earlier 171-test baseline belongs to the initialization report, not this week's execution results.

Learner-authored explanation and mentor sign-off remain pending; assistant-written notes cannot prove personal understanding. This run makes no claim about insurance answer quality, production readiness, actual paid-provider prices or later weeks' completion.

## Short mentor explanation

"Week 01 explains what the model does before we build more features. I can show four real local responses, their token counts, a semantic similarity comparison and a cost calculation. The results illustrate sampling and embeddings, while the limitations show why neither fluency nor similarity proves an answer is true. We reused existing helpers and changed only learning evidence and documentation."
