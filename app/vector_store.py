import asyncio
import hashlib
import chromadb
from app.models import Chunk, SearchResult


class VectorStore:
    """Persistent single-process course store. Original files are not retained."""
    def __init__(self, path: str, collection_name: str, ollama, batch_size: int = 32):
        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection(collection_name, metadata={"hnsw:space": "cosine", "embedding_model": ollama.embed_model})
        self.ollama, self.batch_size = ollama, batch_size
        self._lock = asyncio.Lock()
        # Hybrid search needs the whole corpus for BM25 on every query. Reading it back
        # from Chroma each time dominated query latency, so cache it and bump `version`
        # on every write. Single-process store, so an in-process version is sufficient.
        self.version = 0
        self._chunk_cache: dict[str | None, tuple[int, list[Chunk]]] = {}

    def check_model(self):
        recorded = (self.collection.metadata or {}).get("embedding_model")
        if recorded and recorded != self.ollama.embed_model:
            raise ValueError("Embedding model differs from this collection. Use a new collection and re-index.")

    async def upsert(self, chunks: list[Chunk]) -> None:
        if not chunks:
            raise ValueError("No readable text found. Scanned PDFs need OCR before upload.")
        self.check_model()
        vectors = []
        for offset in range(0, len(chunks), self.batch_size):
            vectors.extend(await self.ollama.embed([c.text for c in chunks[offset:offset + self.batch_size]]))
        async with self._lock:
            def write():
                self.check_model()
                old = self.collection.get(where={"source": {"$in": sorted({c.source for c in chunks})}}, include=[])["ids"]
                for offset in range(0, len(chunks), self.batch_size):
                    batch = chunks[offset:offset + self.batch_size]
                    self.collection.upsert(ids=[c.id for c in batch], documents=[c.text for c in batch],
                        embeddings=vectors[offset:offset + self.batch_size],
                        metadatas=[{**c.metadata, "source": c.source, "page": c.page or 0} for c in batch])
                stale = sorted(set(old) - {c.id for c in chunks})
                if stale:
                    self.collection.delete(ids=stale)
            await asyncio.to_thread(write)
            self._invalidate()

    async def search(self, query: str, k: int, source: str | None = None) -> list[SearchResult]:
        self.check_model()
        count = await asyncio.to_thread(self.collection.count)
        if not count:
            return []
        vector = (await self.ollama.embed([query]))[0]
        kwargs = {"where": {"source": source}} if source else {}
        result = await asyncio.to_thread(self.collection.query, query_embeddings=[vector], n_results=min(k, count),
                                        include=["documents", "metadatas", "distances"], **kwargs)
        rows = []
        for rank, (cid, text, meta, distance) in enumerate(zip(result["ids"][0], result["documents"][0], result["metadatas"][0], result["distances"][0]), 1):
            score = min(1.0, max(0.0, 1.0 - float(distance)))
            rows.append(SearchResult(id=cid, text=text, source=meta["source"], page=meta.get("page") or None,
                                     metadata=meta, score=score, semantic_score=score, rank=rank, retrieval_method="semantic"))
        return rows

    def _invalidate(self) -> None:
        self.version += 1
        self._chunk_cache.clear()

    def all_chunks(self, source: str | None = None) -> list[Chunk]:
        cached = self._chunk_cache.get(source)
        if cached is not None and cached[0] == self.version:
            return list(cached[1])
        data = self.collection.get(include=["documents", "metadatas"], **({"where": {"source": source}} if source else {}))
        rows = [Chunk(id=i, text=t, source=m["source"], page=m.get("page") or None, metadata=m)
                for i, t, m in zip(data["ids"], data["documents"], data["metadatas"])]
        self._chunk_cache[source] = (self.version, rows)
        return list(rows)

    async def delete_source(self, source: str) -> int:
        """Delete every indexed chunk for one exact uploaded filename."""
        async with self._lock:
            ids = await asyncio.to_thread(lambda: self.collection.get(where={"source": source}, include=[])["ids"])
            if ids:
                await asyncio.to_thread(self.collection.delete, ids=ids)
                self._invalidate()
            return len(ids)

    async def clear(self) -> int:
        """Clear the course collection; intended for local learning resets."""
        async with self._lock:
            ids = await asyncio.to_thread(lambda: self.collection.get(include=[])["ids"])
            if ids:
                await asyncio.to_thread(self.collection.delete, ids=ids)
                self._invalidate()
            return len(ids)

    def get_chunk(self, chunk_id: str) -> Chunk | None:
        data = self.collection.get(ids=[chunk_id], include=["documents", "metadatas"])
        if not data["ids"]:
            return None
        meta = data["metadatas"][0]
        return Chunk(id=chunk_id, text=data["documents"][0], source=meta["source"], page=meta.get("page") or None)

    def fingerprint(self) -> str:
        return hashlib.sha256("\n".join(sorted(c.id + ':' + c.text for c in self.all_chunks())).encode()).hexdigest()
