# Week 3 Build an ask my documents application
## Your destination this week

Load documents, retrieve relevant passages, and answer with inspectable sources. If the documents do not establish an answer, the app should say so. The practical deliverable is an HR-policy assistant using the fictional Acorn Labs corpus in this project.

Think of a library helper. The helper first finds the right pages, puts them on the reader's desk, and then asks the reader to answer from those pages. Finding the pages and writing the answer are separate jobs.

**What changed:** multi-file upload support, DOCX table extraction, script-free HTML text extraction, bounded uploads, embedding batches, replacement of stale chunks, source links, structured evidence validation, and a repeatable two-size chunking experiment.

## 1 What RAG does

Retrieval-Augmented Generation adds relevant external information to the input of a generative model. It does not normally retrain that model.

There are two workflows:

**Ingestion:** document bytes → extracted text → chunks → embeddings → persistent index.

**Question answering:** question → retrieval → context construction → model output → validation → answer and sources.

The first workflow can happen hours before the second. If the first workflow loses a table or never indexes a policy addendum, the answer workflow cannot reliably recover that missing evidence.

RAG is useful when answers must come from particular files, when content changes, or when users need provenance. It is not automatically the best choice for arithmetic, database transactions, or tasks better served by direct structured queries.

## 2 Understand the training corpus

The course corpus includes leave, remote work, expenses, security, conduct, benefits, a project-specific addendum, and a malicious-instruction example. Every policy is fictional training material.

The historical corpus remains in knowledge_base. Its handbook contains unresolved template fields and should not be treated as approved real HR policy. We did not replace those placeholders with invented company decisions.

The course uses .txt, .md, and .html fixtures because they are easy to inspect and version. PDF and DOCX extraction are supported and tested separately. You can create your own PDF or DOCX from the same fictional text and upload it to test those paths.

Seed the running course API:

~~~powershell
.\.venv\Scripts\python.exe -m course.run seed
~~~

Open **http://127.0.0.1:8001/documents**. Confirm the expected filenames appear. Then open the home page and ask an annual leave question.

## 3 Loading documents without silently losing facts

A loader turns a file format into usable text:

| Format | Application behavior | Limitation to remember |
|---|---|---|
| PDF | Extract text by page, retain page number | Scanned images need OCR first |
| DOCX | Read paragraphs and tables in order | Headers, footnotes, and complex drawing content are not a complete archival extraction |
| TXT and Markdown | Decode UTF-8 text | Other encodings can produce replacement characters |
| HTML | Remove script/style content and extract visible text | No browser rendering or remote URL fetching |

The app accepts uploaded HTML; it does not crawl arbitrary websites. This avoids quietly adding remote-fetch behavior such as SSRF exposure. Save a permitted web page locally before using it as a learning document.

Empty or unreadable files return a controlled error. File size is limited to 10 MB by default and extracted text to one million characters. Limits prevent some resource problems but do not constitute malware scanning.

**Test:** create a DOCX with a table containing “Expense deadline: 30 days.” Upload it and inspect the extracted evidence. The old loader omitted tables; the upgraded loader includes them.

## 4 Chunking strategies

A chunk is a piece of source text small enough to retrieve and fit into the prompt.

- Fixed-length chunking is predictable but may cut a fact in half.
- Sentence or paragraph chunking respects natural boundaries but produces uneven sizes.
- Recursive splitting tries larger structural boundaries before smaller ones.
- Semantic chunking uses changes in meaning to choose boundaries; it adds cost and tuning.
- Parent-child retrieval searches small child chunks and supplies larger parent sections for context.

The current TextChunker uses character limits, a preferred sentence boundary where available, and word boundaries as fallback. It normalizes whitespace. It does not preserve a full heading hierarchy or perform semantic segmentation.

**Overlap** repeats some characters between neighboring chunks. It reduces the chance that a boundary hides a condition, but increases storage and can return near-duplicate evidence. Overlap must be smaller than chunk size.

Example: a policy says, “Expense claims are due in 30 days. Project ORCHID-77 uses 14 days.” A cut that isolates the exception can make the generic rule look universal. A bigger chunk may keep both together, but it may also mix irrelevant topics.

## 5 Embeddings and dense retrieval

A bi-encoder-style retrieval system independently embeds the question and each document passage. Document embeddings can be computed ahead of time. At query time, the system compares the question vector with stored vectors.

A cross-encoder jointly reads a question-passage pair and scores it. It can inspect interactions more closely, but scoring every document at query time is expensive. A common design uses fast retrieval first and a cross-encoder on a short candidate list second.

This project uses Ollama embeddings for dense search. The same embedding model must be used for indexing and querying. Matching vector dimensions alone is not enough: two unrelated models can both output 768 numbers but use incompatible spaces.

New course collections record the embedding model name. Old legacy collections may lack that provenance; use a new collection when changing models or preparing a controlled experiment. Model tags can be updated in place, so serious reproducibility also records model digests, not just names.

### MTEB BGE and E5

MTEB is an evaluation benchmark collection for embedding tasks. A leaderboard can help shortlist models, but your actual HR questions decide whether one is useful.

BGE and E5 are embedding model families. Some versions require specific query/document prefixes or instructions. For example, the E5 model card documents query and passage prefixes. Applying those conventions to the wrong model can hurt results.

The core app uses nomic-embed-text from the existing environment. It does not claim to benchmark every embedding model. If you switch models, create a new collection and rerun the same cases.

## 6 Vector databases and HNSW

A vector database stores vectors with associated text and metadata and supports similarity queries. In this app, Chroma persists locally.

HNSW is an approximate nearest-neighbor graph method. A useful child-level picture is a map with shortcuts: the search follows promising links instead of checking every location. Approximation trades some recall for speed and memory behavior. HNSW does not itself understand policy meaning; the embedding model supplies the numerical representation.

Chroma is convenient for this local exercise. Qdrant is another vector database option, and pgvector adds vector operations to PostgreSQL. You do not need to implement all three to understand the choice. Evaluate persistence, metadata filters, operational needs, indexing options, and existing infrastructure.

## 7 Similarity search and top K

A similarity search returns the k closest candidates under a distance measure. Our dense search uses cosine distance and exposes a derived similarity score.

Top-k is a tradeoff. Too few chunks can omit an exception. Too many can distract the model or exceed context limits. More retrieved text is not automatically more evidence.

The current default is four answer-context chunks. The inspection endpoint exposes the larger candidate pools and separate lexical and dense signals. A score is a retrieval signal, not a confidence probability.

## 8 Metadata filtering

Metadata describes a chunk, such as filename and page. Filtering can restrict search to a known document.

Example request:

~~~json
{
  "question": "How should emergency leave be requested?",
  "retrieval": {
    "mode": "hybrid",
    "k": 4,
    "source": "leave-policy.txt"
  }
}
~~~

Use this with POST /inspect or POST /ask.

Filtering is helpful for debugging, but choosing a filter because you already know the answer is a form of evaluation leakage if the real user will not provide it. Also, a filename filter is not tenant authorization. Production document access must be enforced independently.

## 9 Grounded generation and source links

The model receives numbered contexts. It returns claims with exact supporting quotes. Python checks quote membership and source bounds and renders source links such as /sources/CHUNK_ID.

Clicking a source link opens the stored chunk with its filename and page. The app does not retain the original uploaded binary, so this is a source-excerpt link, not a download of the complete PDF.

After replacing a document, a previous chunk link may return 404. This makes the lack of historical source version retention visible. For immutable audit links, add document version storage before production use.

A genuine unknown returns exactly:

“I don't know based on the uploaded documents.”

No citation or high confidence is attached to that abstention. A model can still miss an answerable question or misinterpret evidence; those failures belong in the evaluation set.

## 10 Document replacement

Re-uploading the same filename replaces stale chunks from that source after new embeddings have been produced. Re-uploading identical content is idempotent at the chunk-ID level.

This fixes the previous behavior where both old and revised leave allowances remained searchable. If embedding fails before writing, the old document stays available.

The local write sequence is not a multi-document database transaction. A process crash during batched writes can leave partial state. This is a known production limitation, not a guarantee of atomic version replacement.

## 11 Run the chunk-size experiment

~~~powershell
.\.venv\Scripts\python.exe -m course.run week3
~~~

This creates separate collections for 400-character and 900-character chunks. Overlap stays at 50 characters in both arms. The corpus, models, questions, retrieval mode, and k stay fixed.

Read **course/results/week3_retrieval.json**. Compare chunk count, hit-rate@3, MRR, and individual retrieved passages.

The measured first run tied at hit-rate@3 = 1.0 for both sizes. That means this small source-level test did not distinguish them. It does not prove equal answer completeness or equal performance on longer documents.

**Extend the test honestly:** add a longer fictional addendum with a condition near a boundary. Decide the expected evidence before running. Do not keep editing questions until one chunk size wins.

## 12 Quick test plan

| Scenario | What you should inspect |
|---|---|
| Annual leave question | 20-day evidence and a valid source link |
| Dental premium question | Exact abstention |
| ORCHID-77 expenses | 14-day project exception, not just generic 30 days |
| Repeat the same upload | No duplicate chunk accumulation |
| Revise a same-named file | Old statement disappears from retrieval |
| Empty or scanned document | Controlled unreadable-text error |
| Query with filename filter | Only that source appears |
| Malicious instruction | No adoption of the 999-day policy |

Run the automated tests with **.\\run_evals.ps1**. Use the inspection screen for manual evidence checks; a passing unit suite is not a complete model evaluation.

## 13 Friday explanation and self-check

Demonstrate upload, a supported answer, a source link, an unknown question, and the two-size experiment. Explain why the no-gain result is still useful.

**Questions:** Does RAG train the chat model? No. Can the wrong loader cause a retrieval failure? Yes. Does a high cosine score prove a policy statement? No. Is source-level hit-rate enough to prove the right paragraph was retrieved? No.

## References

- [Retrieve and rerank with bi-encoders and cross-encoders](https://www.sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html)
- [E5 model instructions](https://huggingface.co/intfloat/e5-small-v2)
