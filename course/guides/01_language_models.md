# Week 1 How language models work
## Your destination this week

This is the theory-only week. You do not need to write or run Python. By the end, you should be able to explain how a model makes a sentence, why an answer can sound certain and still be wrong, how tokens affect a bill, and why searching your documents is different from training a model.

Imagine a very experienced sentence-completion player. You say, “The kitten drank some…” and the player considers “milk,” “water,” and many other endings. A language model performs a numerical version of that task. The analogy helps you begin, but a modern model learns much richer patterns than a simple phrase lookup.

**What was done in the application:** the code already separated the chat model from the embedding model. We kept that separation, added actual Ollama usage counters to traces, documented sampling, and added optional demonstrations for later weeks. None of these demonstrations is compulsory coding for Week 1.

## 1 From text to an answer

A simplified decoder language model follows this sequence:

1. A tokenizer converts text into token IDs.
2. An embedding table converts each ID into a numerical representation.
3. Transformer layers combine representations using attention and other learned operations.
4. The output layer produces a score, called a logit, for each possible next token.
5. A decoding rule selects one token.
6. The new token is appended, and the process repeats until a stop condition.

During training, the system adjusts weights to improve predictions over many examples. During ordinary inference, those weights are usually fixed. Asking a question does not normally retrain the model. Putting a handbook in the prompt gives it temporary evidence; indexing that handbook gives the application searchable data.

The model learns from a mixture of sources determined by its maker. “All models were trained only on public internet text” is too broad. Training may involve licensed data, code, human-created examples, and other data. Whatever the mix, it does not guarantee knowledge of your private files.

**Explain it to a child:** training is practicing with many books; inference is answering now; retrieval is being allowed to open the right book before answering.

## 2 Tokens and tokenization

A token can be a whole word, a word fragment, punctuation, whitespace, or part of a non-English character sequence. The exact split depends on the tokenizer. The word “unbelievable” might be represented by one token in one tokenizer and several in another.

A token ID is a label in a vocabulary. The ID itself is not the word's meaning. Meaning-related representations come from learned vectors and subsequent processing.

Do not assume one word equals one token. The rough English heuristic of about four characters per token is an estimate, not a billing measurement. Code, numbers, punctuation, and different languages can behave very differently.

**Token budget exercise:** imagine the input contains 200 instruction tokens, 100 question tokens, and four document chunks of 250 tokens each. The input is approximately 1,300 tokens before any additional message-format overhead. A 200-token answer makes approximately 1,500 processed tokens across input and output. A retry processes additional tokens too.

Our application's chunk size is measured in **characters**, not model tokens. A 900-character chunk is not a 900-token chunk.

## 3 The context window

The context window is the model's working space for a request. It includes the instructions, supplied conversation, retrieved evidence, and room needed for output, subject to the model/runtime's accounting rules.

Think of a desk. A bigger desk fits more paper, but filling it with irrelevant paper does not necessarily improve the answer. Important text can still be overlooked. A model's advertised maximum context is also different from the context actually configured in a local runtime.

This application does not remember a conversation automatically. Each request supplies a question and retrieved chunks. The vector database persists documents, but persistence is not conversational memory and does not alter model weights.

**Check your understanding:** if the answer is present in a file on your laptop but the application never loads or retrieves that file, should the model know it? No.

## 4 Temperature and sampling

Temperature changes the sharpness of the next-token distribution. It does not insert facts or measure confidence.

Suppose four possible next tokens have probabilities 0.60, 0.25, 0.10, and 0.05. Greedy decoding chooses the largest. Sampled decoding draws from a distribution, so a less likely token can be selected.

Lower temperature generally makes strong candidates dominate more. Higher temperature generally spreads probability more widely. Temperature zero is commonly used for greedy-like behavior in serving APIs; it is not a universal promise of byte-for-byte reproducibility. Hardware, runtime, model version, and other settings matter.

**Top-k sampling** keeps a fixed number of likely token candidates. If k is 2, the other candidates are excluded.

**Top-p sampling**, also called nucleus sampling, keeps the smallest probability-ranked prefix whose cumulative mass reaches p. With p = 0.8, the first two candidates in our example reach 0.85.

These are generation settings. **Retrieval top-k is different:** it is the number of document chunks returned by search.

**No-code experiment:** ask a model to invent a bakery name three times. Then ask a factual handbook question three times. Record variation and correctness separately. A creative name can vary usefully; a policy deadline should not drift. Do not infer that variation alone proves hallucination.

## 5 Embeddings and meaning

An embedding represents something as a vector: a list of numbers. A useful text embedding places related texts near each other according to a chosen similarity measure.

“Annual leave allowance” and “How much vacation do I receive?” can have high similarity even though they share few words. “A bicycle has two wheels” should usually be less similar, but the actual result depends on the embedding model.

Cosine similarity measures the angle between vectors:

cosine similarity = dot product of vectors / product of their lengths.

It is not the probability that an answer is true. High similarity can connect contradictory sentences: “Leave is 20 days” and “Leave is not 20 days” discuss the same subject.

### Word2Vec and GloVe

Word2Vec learns static word vectors from local word-context prediction tasks. CBOW predicts a target word from surrounding words; skip-gram predicts context words from a target.

GloVe learns vectors using global word co-occurrence statistics. Both approaches make useful patterns in language available to numerical algorithms.

A **static embedding** normally gives a word the same vector wherever it appears. “Bank” in a river sentence and a finance sentence therefore shares the same word lookup vector in a basic static model.

A **contextual representation** changes with surrounding words. Transformer hidden states can represent the financial bank differently from the river bank. A sentence embedding then pools or otherwise derives a representation for a whole text. A contextual token representation and a sentence embedding are related concepts, not identical objects.

The project's Ollama embedding model produces representations for chunks and questions. It is not a Word2Vec or GloVe implementation.

## 6 Encoder and decoder models

An encoder is commonly used to understand an input and create representations, often using bidirectional attention. A decoder is commonly used for autoregressive generation, predicting the next token from available preceding context. Encoder-decoder models combine both patterns.

This is a useful design distinction, not a rule that every embedding model must have one architecture. Decoder-based embedding systems also exist.

GPT, Claude, and Llama are model families, not interchangeable versions of one model. Different models within a family vary in size, capabilities, licensing, runtime support, and costs. Our active local chat model is llama3.2:3b; our embedding model is nomic-embed-text:latest. The code defaults may differ from the values loaded from the local environment.

## 7 Hallucination and apparent confidence

A hallucination is an unsupported or false generated claim. Causes include missing evidence, misleading context, ambiguous instructions, distribution gaps, and generation behavior.

Fluent wording is not verification. “The rule is definitely 30 days” and “Maybe it is 30 days” can both be wrong. Likewise, an API field named confidence is only meaningful if its definition and calibration justify it.

The previous app labelled an unknown dental-premium answer “high” because a retrieved chunk ranked strongly. The upgraded app uses low confidence for abstentions and medium for validated evidence-backed output. Medium is a conservative category, not a calibrated probability.

RAG reduces some unsupported answers but does not eliminate hallucination. Exact-quote checking proves that a quote appears in a chunk; it does not prove that the generated statement follows from that quote.

## 8 Costs and choosing a model

For a simple hosted model with separate input and output prices:

cost = input tokens × input price per million / 1,000,000
+ output tokens × output price per million / 1,000,000.

**Hypothetical arithmetic, not vendor pricing:** at $1 per million input tokens and $4 per million output tokens, 2,000 input tokens plus 500 output tokens cost $0.004. One thousand such calls cost $4 before other charges.

Include embeddings, retries, judges, query rewriting, and reranking in your budget. Some services separately price caching, tools, or other usage. Local Ollama does not charge a hosted per-token API fee for these local calls, but hardware, electricity, memory, and time still cost something.

Choose a model by measuring the job: answer quality on your cases, structured-output reliability, latency, memory, privacy requirements, context needs, and total cost. Do not choose only by a public leaderboard or parameter count.

Price sheets change. Check the official provider's current price sheet before making a budget. This guide uses hypothetical rates so the arithmetic stays valid without pretending a dated price is current.

## 9 Where to look in this project

- **app/ollama_client.py:** separate chat and embedding requests; actual token counts when Ollama returns them.
- **app/config.py:** active model names and retrieval settings.
- **course/labs/foundations.py:** optional numerical and live demonstrations for Week 2 onward.
- **course/results/ask_traces.jsonl:** model call counts from requests to the course API.

Later, you can run:

~~~powershell
.\.venv\Scripts\python.exe -m course.labs.foundations sampling
.\.venv\Scripts\python.exe -m course.labs.foundations cost
.\.venv\Scripts\python.exe -m course.labs.foundations embeddings
.\.venv\Scripts\python.exe -m course.labs.foundations temperature
~~~

The sampling distribution is explicitly invented teaching data. The live embedding similarities and Ollama usage counts are measured.

## 10 Friday self-check

Explain these aloud without opening the code:

1. What changes during training but normally stays fixed during inference?
2. Why is “one word equals one token” unreliable?
3. Can raising temperature repair missing handbook evidence?
4. What is the difference between an embedding and a generated answer?
5. Why can two contradictory sentences have similar embeddings?
6. Why does local inference still have a cost?

**Answer key:** weights; tokenization varies; no; numerical representation versus text generation; semantic subject overlap; hardware and operating resources.

**Deliverable:** one page of your own explanations, a hypothetical cost calculation, and observations from a small no-code experiment. No programming submission is required this week.

## References

- [GloVe project and paper](https://nlp.stanford.edu/projects/glove/)
- [Ollama sampling parameter reference](https://docs.ollama.com/modelfile)
- [Ollama generation API](https://docs.ollama.com/api/generate)
