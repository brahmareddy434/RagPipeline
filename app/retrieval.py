import asyncio
import re
from functools import lru_cache
import numpy as np
from rank_bm25 import BM25Plus
from app.models import Chunk, RetrievalOptions, SearchResult


def tokenize(text: str) -> list[str]:
    return re.findall(r"[^\W_]+(?:[-_][^\W_]+)*", text.lower(), re.UNICODE)


class KeywordRetriever:
    """Cache BM25 by corpus content; ignore documents without a query term."""
    def __init__(self):
        self._signature = None
        self._index = None

    def search(self, query: str, chunks: list[Chunk], k: int, key=None) -> list[SearchResult]:
        """`key` is an O(1) corpus version token supplied by a store that tracks writes.

        Without one, fall back to hashing the corpus content: callers may reuse a retriever
        across unrelated corpora that happen to share chunk ids.
        """
        tokens = tokenize(query)
        if not chunks or not tokens:
            return []
        signature = ("key", key) if key is not None else ("content", tuple((c.id, c.text) for c in chunks))
        if signature != self._signature:
            self._tokens = [tokenize(c.text) for c in chunks]
            self._index = BM25Plus(self._tokens, delta=0) if any(self._tokens) else None
            self._signature = signature
        if self._index is None:
            return []
        scores = self._index.get_scores(tokens)
        order = sorted((i for i in range(len(chunks)) if scores[i] > 0), key=lambda i: (-scores[i], chunks[i].id))[:k]
        return [SearchResult(**chunks[i].model_dump(), score=0, keyword_score=float(scores[i]),
                             rank=rank, retrieval_method="keyword") for rank, i in enumerate(order, 1)]


@lru_cache(maxsize=1)
def cross_encoder(model_name: str):
    try:
        from sentence_transformers import CrossEncoder
    except ImportError as exc:
        raise ValueError("Cross encoder needs requirements-optional.txt; see Week 4 guide.") from exc
    return CrossEncoder(model_name)


class HybridRetriever:
    def __init__(self, store, keyword: KeywordRetriever, rrf_constant: int = 60,
                 reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.store, self.keyword, self.rrf_constant = store, keyword, rrf_constant
        self.reranker_model = reranker_model
        self._keyword_lock = asyncio.Lock()

    async def inspect(self, query: str, options: RetrievalOptions):
        search_query = query
        if options.query_transform != "none":
            instruction = ("Rewrite as a concise search query. Preserve names, codes and intent. Return only the query."
                           if options.query_transform == "rewrite" else
                           "Write a short hypothetical passage that might answer the question, only for retrieval. This is not factual evidence.")
            search_query = (await self.store.ollama.chat([
                {"role": "system", "content": instruction}, {"role": "user", "content": query}], 0))[:2000]
        pool = max(options.k * 3, 10)

        async def semantic_arm():
            return await self.store.search(search_query, pool, options.source) if options.mode != "keyword" else []

        async def keyword_arm():
            if options.mode == "semantic":
                return []
            chunks = await asyncio.to_thread(self.store.all_chunks, options.source)
            version = getattr(self.store, "version", None)
            key = (options.source, version) if version is not None else None
            # One shared BM25 index, so serialise rebuilds; the embedding call runs concurrently.
            async with self._keyword_lock:
                return await asyncio.to_thread(self.keyword.search, query, chunks, pool, key)

        semantic, keyword = await asyncio.gather(semantic_arm(), keyword_arm())
        if options.mode == "hybrid":
            combined = {}
            for rows in (semantic, keyword):
                for item in rows:
                    current = combined.setdefault(item.id, item.model_copy(deep=True))
                    current.fusion_score += 1 / (self.rrf_constant + item.rank)
                    current.semantic_score = max(current.semantic_score, item.semantic_score)
                    current.keyword_score = max(current.keyword_score, item.keyword_score)
                    current.score = current.semantic_score
                    current.retrieval_method = "hybrid_rrf"
            results = sorted(combined.values(), key=lambda r: (-r.fusion_score, r.id))
        else:
            results = semantic or keyword
        if options.rerank == "cross_encoder" and results:
            def rerank():
                model = cross_encoder(self.reranker_model)
                return [float(s) for s in model.predict([(query, r.text) for r in results])]
            scores = await asyncio.to_thread(rerank)
            results = [r.model_copy(update={"rerank_score": s}) for r, s in zip(results, scores)]
            results.sort(key=lambda r: r.rerank_score, reverse=True)
        elif options.rerank == "mmr" and results:
            vectors = np.asarray(await self.store.ollama.embed([query] + [r.text for r in results]))
            vectors = vectors / np.maximum(np.linalg.norm(vectors, axis=1, keepdims=True), 1e-12)
            relevance = vectors[1:] @ vectors[0]
            similarity = vectors[1:] @ vectors[1:].T
            selected, remaining = [], list(range(len(results)))
            while remaining and len(selected) < options.k:
                best = max(remaining, key=lambda i: .7 * relevance[i] - .3 * max((similarity[i, j] for j in selected), default=0))
                selected.append(best)
                remaining.remove(best)
            results = [results[i] for i in selected]
        results = [r.model_copy(update={"rank": i}) for i, r in enumerate(results[:options.k], 1)]
        return results, {"question": query, "search_query": search_query, "options": options.model_dump(),
                         "semantic": [r.model_dump() for r in semantic], "keyword": [r.model_dump() for r in keyword],
                         "note": "Scores rank evidence; they are not probabilities of answer correctness."}

    async def search(self, query: str, k: int, options: RetrievalOptions | None = None):
        return (await self.inspect(query, options or RetrievalOptions(k=k)))[0]
