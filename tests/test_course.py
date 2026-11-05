import io
import json
import httpx
import pytest
from docx import Document
from fastapi.testclient import TestClient
from app.schemas import Chunk, GroundedAnswer, RetrievalOptions
from app.rag.loading import DocumentLoader
from app.rag.retrieval import KeywordRetriever, HybridRetriever
from app.services.tools import Calculator
from app.infrastructure.ollama import OllamaClient, OllamaUnavailable
from app.repositories.vector_store import VectorStore
from app.rag.chunking import TextChunker
from app.config.settings import Settings


@pytest.mark.parametrize("expression",["1/0","2+","2**99999999","True+2","1e309","(-1)**0.5","abs(1)"])
def test_unsafe_arithmetic_is_controlled(expression):
    with pytest.raises(ValueError):
        Calculator().run(expression)


def test_docx_table_and_html_script_handling():
    doc = Document(); doc.add_table(rows=1,cols=1).cell(0,0).text="Policy table"
    buffer=io.BytesIO(); doc.save(buffer)
    assert "Policy table" in DocumentLoader().load("p.docx",buffer.getvalue())[0][1]
    assert "alert" not in DocumentLoader().load("p.html",b"<script>alert(1)</script><p>Policy</p>")[0][1]


def test_keyword_empty_unmatched_and_unicode():
    search=KeywordRetriever()
    assert search.search("query",[Chunk(id="1",text="!!!",source="a")],3) == []
    assert search.search("unrelated",[Chunk(id="1",text="leave policy",source="a")],3) == []
    assert search.search("政策",[Chunk(id="1",text="政策",source="a")],3)[0].id == "1"
    assert search.search("leave",[Chunk(id="1",text="leave policy",source="a")],3)[0].score == 0


def test_settings_overlap():
    with pytest.raises(ValueError):
        Settings(chunk_size=200,chunk_overlap=200)


def test_swagger_source_placeholder_means_no_filter():
    assert RetrievalOptions(source="string").source is None
    assert RetrievalOptions(source="   ").source is None


def test_contradictory_answerability_rejected():
    with pytest.raises(ValueError):
        GroundedAnswer(answerable=True,claims=[])
    with pytest.raises(ValueError):
        GroundedAnswer(answerable=False,claims=[{"statement":"A supported rule.","context_number":1,"quote":"A supported rule."}])


class FakeEmbed:
    embed_model="fake-v1"
    async def embed(self,texts):
        return [[1.,float(len(t)%7+1),.5] for t in texts]


async def test_document_replacement_and_filter(tmp_path):
    store=VectorStore(str(tmp_path/"chroma"),"test_course",FakeEmbed(),2)
    chunks=TextChunker(200,30)
    await store.upsert(chunks.split("policy.txt",[(None,"Employees receive 20 days.")]))
    await store.upsert(chunks.split("policy.txt",[(None,"Employees receive 25 days.")]))
    assert [r.text for r in store.all_chunks()] == ["Employees receive 25 days."]
    assert await store.search("leave",3,"missing.txt") == []
    assert store.get_chunk(store.all_chunks()[0].id).source == "policy.txt"
    store.ollama.embed_model="different"
    with pytest.raises(ValueError):
        await store.search("leave",3)


async def test_failed_embedding_keeps_previous_document(tmp_path):
    store=VectorStore(str(tmp_path/"chroma"),"test_failure",FakeEmbed())
    await store.upsert([Chunk(id="old",text="Old policy",source="p.txt")])
    async def broken(texts):
        raise OllamaUnavailable("offline")
    store.ollama.embed=broken
    with pytest.raises(OllamaUnavailable):
        await store.upsert([Chunk(id="new",text="New policy",source="p.txt")])
    assert store.all_chunks()[0].id == "old"


async def test_ollama_retries_validation_without_mutating_input():
    client=OllamaClient("http://test","chat","embed")
    await client.http.aclose()
    calls=[]
    def handler(request):
        calls.append(json.loads(request.content))
        content="broken" if len(calls)==1 else '{"answerable":false,"claims":[]}'
        return httpx.Response(200,json={"message":{"content":content}})
    client.http=httpx.AsyncClient(transport=httpx.MockTransport(handler))
    messages=[{"role":"user","content":"test"}]
    try:
        result=await client.structured(messages,GroundedAnswer)
        assert not result.answerable and len(calls)==2 and len(messages)==1
    finally:
        await client.close()


async def test_ollama_connection_error_is_503_type():
    client=OllamaClient("http://test","chat","embed")
    await client.http.aclose()
    def handler(request):
        raise httpx.ConnectError("offline",request=request)
    client.http=httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(OllamaUnavailable):
            await client.health()
    finally:
        await client.close()


def test_api_validation_upload_source_and_trace(tmp_path,monkeypatch):
    import app.main as main
    from app.bootstrap import Container
    original=Container.build.__func__
    def build(cls,settings):
        c=original(cls,settings)
        c.store.ollama.embed=FakeEmbed().embed
        async def grounded(messages,schema,**kwargs):
            return GroundedAnswer(answerable=False)
        c.ollama.structured=grounded
        return c
    monkeypatch.setattr(main,"get_settings",lambda:Settings(chroma_path=tmp_path/"db",trace_log_path=tmp_path/"traces.jsonl",collection_name="api_test"))
    monkeypatch.setattr(Container,"build",classmethod(build))
    with TestClient(main.app) as client:
        assert client.post("/ask",json={"question":"  "}).status_code == 422
        assert client.post("/documents",files={"file":("x.exe",b"x")}).status_code == 415
        assert client.post("/documents",files={"file":("x.txt",b"")}).status_code == 400
        assert client.post("/documents",files={"file":("x.txt",b"Employees receive twenty days leave.")}).status_code == 200
        response=client.post("/ask",json={"question":"What is the leave?"})
        assert response.status_code==200 and response.headers["x-trace-id"]
        chunk=response.json()["retrieved"][0]
        assert client.get("/sources/"+chunk["id"]).status_code==200
        assert client.get("/sources/missing").status_code==404
    assert len((tmp_path/"traces.jsonl").read_text().splitlines())==1


def test_vector_store_clear_and_delete_source(tmp_path):
    import asyncio
    store=VectorStore(str(tmp_path/"chroma_clear"),"clear_test",FakeEmbed())
    asyncio.run(store.upsert([Chunk(id="a",text="A",source="a.txt"),Chunk(id="b",text="B",source="b.txt")]))
    assert asyncio.run(store.delete_source("a.txt")) == 1
    assert [x.source for x in store.all_chunks()] == ["b.txt"]
    assert asyncio.run(store.clear()) == 1
    assert store.all_chunks() == []
