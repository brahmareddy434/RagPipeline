# Week 4 Diagnose retrieval and measure one change
## Your destination this week

Take failing questions, show where each failure occurs, make one controlled improvement, and calculate a before-and-after result. Do not change five settings at once and guess which helped.

Imagine a student answers the wrong question because the librarian handed over the wrong book. A better writer does not fix that. But if the correct page is on the desk and the student ignores an exception, the failure is in answering rather than finding.

**What changed:** a side-by-side inspection screen, semantic/keyword/hybrid modes, separate score fields, Unicode-safe BM25, MMR, optional cross-encoder reranking, query rewriting, HyDE, and a repeatable single-variable retrieval experiment.

## 1 Classify the actual failure

Read the question, all retrieved chunks, and the final answer.

**Retrieval failure:** supporting evidence exists in the corpus but does not appear in the retrieved set.

**Generation failure:** the required evidence is in the retrieved set, but the answer omits, distorts, or contradicts it.

There are other useful categories: source quality, document loading, invalid expected labels, and unsupported questions. Do not force every problem into retrieval or generation if the document itself is an unapproved template.

A filename match is weaker than an evidence match. Retrieving a handbook's table of contents is not equivalent to retrieving its emergency-leave paragraph.

## 2 Use the inspection screen

Open **http://127.0.0.1:8001/**.

The three columns show question/search settings, retrieved evidence, and final answer/citations. “Inspect retrieval” makes no answer-generation call. “Ask with evidence” runs both retrieval and generation.

The full data includes dense candidates, keyword candidates, final fused results, transformed query if any, and score fields.

Read the actual text, not just rank 1. An exception at rank 3 can be essential. A citation number should map to the chunk that supports the associated claim.

## 3 Keyword search and BM25

Keyword search rewards exact term overlap. It is useful for IDs, error codes, unusual names, and precise policy language.

BM25 combines term frequency, inverse document frequency, and document-length normalization. Repeating a term helps less and less rather than increasing the score without bound. A rare useful term can be more informative than a common word.

The current implementation uses the BM25Plus family with delta zero. It caches its index by chunk content, handles an empty token corpus, and excludes nonpositive matches. It does not normalize the strongest keyword hit into a confidence of one.

The tokenizer supports Unicode word characters and preserves internal hyphens/underscores in codes. Tokenization is still language-dependent; a simple regular expression is not a high-quality segmenter for every language.

## 4 Dense versus keyword retrieval

Dense search can connect vacation with leave or fixing a bike with bicycle repair. Keyword search can preserve exact ERR-4032.

Neither dominates every task. Dense search can confuse similar policies. Keyword search can miss a paraphrase with no shared terms. Both depend on source quality.

Try “How much vacation annually?” in keyword mode and hybrid mode. Then inspect “How do I resolve ERR-4032?” Compare actual evidence, not only the score.

## 5 Reciprocal rank fusion

RRF combines ranked lists without assuming their raw scores share a scale:

RRF(document) = sum over lists of 1 / (constant + rank).

Our constant is 60. A document appearing near the top of both lists receives contributions from both.

Illustration: rank 1 contributes 1/61, and rank 3 contributes 1/63. The sum is about 0.0323. Those numbers are ordering signals, not probabilities.

The upgraded code stores semantic_score, keyword_score, and fusion_score separately. Zero-match keyword entries are not allowed to gain an RRF vote merely because they were returned in a fixed-length list.

Hybrid search still does not guarantee relevance. It merges imperfect candidate lists.

## 6 Reranking with a cross-encoder

A cross-encoder reads the question and each candidate passage together. It produces a pair score, often improving the ordering of a small candidate set.

It cannot rescue a relevant passage that never entered the candidate set. Candidate recall is therefore the first prerequisite.

The app has a real optional Sentence Transformers integration:

~~~powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-optional.txt
.\.venv\Scripts\python.exe -m course.labs.optional_integrations cross_encoder
~~~

After installation and model download, choose cross_encoder on the inspection screen. The default model is cross-encoder/ms-marco-MiniLM-L-6-v2. Set RERANKER_MODEL before startup to try a compatible alternative such as a BGE reranker. Model download size and hardware cost are separate from the core app.

Cohere Rerank is an external hosted alternative. The optional demo reads COHERE_API_KEY from the environment and sends a short demonstration query. Do not send confidential HR documents to an external provider without authorization.

~~~powershell
.\.venv\Scripts\python.exe -m course.labs.optional_integrations cohere
~~~

No external paid call was made merely to satisfy this course.

## 7 MMR and diversity

Maximal Marginal Relevance balances relevance to the query against similarity to already selected passages:

candidate value = lambda × query similarity
− (1 − lambda) × maximum similarity to a selected passage.

The implementation uses lambda 0.7. A high value prioritizes relevance; a lower value favors diversity.

Imagine the top four chunks are nearly identical overlapping sections of the leave policy. MMR may replace a duplicate with a separate exception. That can help, but diversity can also push out a useful near-duplicate. Measure the tradeoff.

Choose mmr under second pass, inspect which chunks changed, and record whether the necessary condition remained.

## 8 Query rewriting

A rewrite turns a messy question into a cleaner search query while trying to preserve names, codes, and intent.

Example: “umm my claim thing ORCHID-77 when must i send?” might become “ORCHID-77 expense claim submission deadline.”

The app exposes the rewritten query. The original question remains the user's question for generation. Keyword search keeps the original query so exact identifiers are not silently lost.

A rewrite can change meaning or erase negation. Always compare the transformed query and measure whether it helps. It adds a model call and can increase latency substantially on local hardware.

## 9 HyDE

Hypothetical Document Embeddings generates a short hypothetical answer-like passage, embeds it, and retrieves real passages nearby.

The hypothetical text is a search aid. It must never be used as evidence or stored as an approved policy. In this app, only retrieved source chunks enter the answer context.

HyDE may bridge a vocabulary gap, but it can also invent an assumption that steers retrieval away from the right policy. It costs an additional model call. Keep it off unless a measured experiment justifies it.

Do not call every query rewrite HyDE: the hypothetical-document step is the distinguishing idea.

## 10 Metrics you can calculate by hand

Suppose four answerable questions find a relevant source at ranks 1, 3, missing, and 2.

**Hit-rate@3:** three of four questions have at least one relevant result, so 3/4 = 0.75.

**MRR@3:** average reciprocal rank, counting misses as zero:
(1 + 1/3 + 0 + 1/2) / 4 = approximately 0.4583.

**Recall@3:** fraction of all relevant items retrieved. If a question has two relevant sources and only one is returned, source-level recall is 1/2 even though hit-rate for that question is one.

Choose the evaluation unit: documents, chunks, or annotated evidence spans. This app's endpoint uses source-level labels. With one relevant source per case, source recall equals hit rate. Do not pretend it measures all relevant passages.

Precision asks what fraction of returned items are relevant. It answers a different question from recall.

Out-of-scope questions have no relevant source. Evaluate their abstention separately instead of fabricating a retrieval rank.

## 11 The single-change experiment

Run:

~~~powershell
.\.venv\Scripts\python.exe -m course.run week4
~~~

The before arm uses keyword retrieval. The after arm uses hybrid retrieval. Chunk size stays 900, overlap stays 50, k stays 3, and the corpus/questions/models stay fixed.

Read **course/results/week4_retrieval.json**. It contains each question's rank and actual retrieved text.

The measured initial result was:

| Metric | Keyword before | Hybrid after |
|---|---:|---:|
| Hit-rate@3 | 15/17 = 88.2% | 17/17 = 100% |

The two recovered paraphrases demonstrate why meaning-based retrieval helps this particular set. The result does not establish performance on every HR corpus. The cases are curated training cases, not a random sample of real employee traffic.

A source-level perfect score still leaves generation errors possible. Week 6 measures the answers separately.

## 12 Build an honest failure record

For every failure, record:

- Question and expected source/evidence.
- Actual retrieved chunks and their order.
- Whether the relevant passage is present.
- Final answer and the specific defect.
- Primary failure category.
- The proposed single change and predicted effect.

Example from historical traces: a manager-involved harassment question retrieved the HR-routing exception at rank 2 but answered with the generic manager route. That is a generation failure. Adding hybrid retrieval alone would not fix it.

Example from the course experiment: a paraphrase with no keyword overlap returned no relevant keyword result, while hybrid retrieval found the leave source. That is retrieval improvement.

## 13 What your change did not fix

Record unchanged failures as carefully as recovered ones. A retrieval change cannot approve unresolved policy placeholders, guarantee semantic faithfulness, fix missing original-file storage, or validate a human grading rubric.

This week's measured hybrid change fixed the two source misses in the small course set. It did not prove that every answer contains every exception, that citations support every statement, or that a judge is reliable.

## 14 Friday demonstration

Show one concrete failure, the evidence that classifies it, the one setting changed, before/after ranks, and the resulting metric. Then name a failure category the change cannot solve.

**Self-check:** Can a reranker find a missing candidate? No. Is an RRF score a probability? No. Is HyDE output a source? No. Can source hit-rate be perfect while the answer is wrong? Yes.

## References

- [Sentence Transformers retrieval and reranking](https://www.sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html)
- [Cohere rerank API](https://docs.cohere.com/v2/reference/rerank)
- [HyDE paper](https://arxiv.org/abs/2212.10496)
