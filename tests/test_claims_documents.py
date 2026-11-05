import pytest
from app.services.ingestion import IngestionService
from app.rag.loading import DocumentLoader
from app.rag.chunking import TextChunker
from app.repositories.vector_store import VectorStore
from app.infrastructure.ollama import OllamaUnavailable

class Embeddings:
    embed_model="fixture"
    fail=False
    async def embed(self,texts):
        if self.fail: raise OllamaUnavailable("fixture outage")
        return [[1.,.5,.2] for _ in texts]

async def test_reindex_versions_and_failed_provider_preserve_index(tmp_path):
    provider=Embeddings(); store=VectorStore(str(tmp_path),"claims_test",provider)
    service=IngestionService(DocumentLoader(),TextChunker(400,80),store)
    await service.ingest([("policy.txt",b"Fictional motor deductible is 500.")])
    old=store.all_chunks()[0]; saved=store.get_chunk(old.id)
    assert len(saved.metadata["document_version"])==64 and saved.metadata["embedding_model"]=="fixture"
    provider.fail=True
    with pytest.raises(OllamaUnavailable): await service.ingest([("policy.txt",b"Changed deductible is 600.")])
    assert store.get_chunk(old.id).text==old.text
    provider.fail=False
    await service.ingest([("policy.txt",b"Changed deductible is 600.")])
    assert store.get_chunk(old.id) is None
    assert store.all_chunks()[0].metadata["document_version"] != old.metadata["document_version"]

async def test_empty_batch_member_does_not_partially_write(tmp_path):
    store=VectorStore(str(tmp_path),"claims_test",Embeddings())
    service=IngestionService(DocumentLoader(),TextChunker(400,80),store)
    with pytest.raises(ValueError): await service.ingest([("valid.txt",b"Valid policy."),("empty.txt",b" ")])
    assert store.all_chunks()==[]
