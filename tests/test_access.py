import hashlib
import pytest
from fastapi.testclient import TestClient
from app.config.settings import Settings
from app.main import create_app
from app.bootstrap import Container


def auth_settings(tmp_path, **kwargs):
    digest = lambda value: hashlib.sha256(value.encode()).hexdigest()
    return Settings(_env_file=None, chroma_path=tmp_path / "db", trace_log_path=tmp_path / "traces.jsonl",
        access_mode="authenticated", api_token_hashes={
            digest("test-alpha"): {"tenant": "alpha", "role": "admin"},
            digest("test-beta"): {"tenant": "beta", "role": "admin"},
            digest("test-reader"): {"tenant": "alpha", "role": "reader"},
        }, **kwargs)


def test_remote_local_mode_and_host_rejected():
    client = TestClient(create_app(Settings(_env_file=None)), client=("203.0.113.10", 9))
    assert client.get("/api/v1/session").status_code == 403
    local = TestClient(create_app(Settings(_env_file=None)), client=("127.0.0.1", 9))
    assert local.get("/api/v1/session").json()["tenant"] == "local"
    assert local.get("/api/v1/session", headers={"host": "attacker.example"}).status_code == 400
    assert local.post("/tools/run", json={"question": "2+3"}, headers={"origin": "https://attacker.example"}).status_code == 403


def test_auth_roles_limits_and_validation(tmp_path):
    client = TestClient(create_app(auth_settings(tmp_path, requests_per_minute=3)))
    assert client.get("/api/v1/session").status_code == 401
    reader = {"Authorization": "Bearer test-reader"}
    assert client.delete("/api/v1/documents/a.txt", headers=reader).status_code == 403
    for _ in range(3):
        assert client.get("/api/v1/session", headers=reader).status_code == 200
    assert client.get("/api/v1/session", headers=reader).status_code == 429
    beta = {"Authorization": "Bearer test-beta"}
    response = client.post("/api/v1/tools/run", json={"question": ""}, headers=beta)
    assert response.status_code == 422
    assert "input" not in response.json()["detail"][0]
    assert response.headers["x-request-id"]


def test_tenant_source_and_memory_collections_are_isolated(tmp_path, monkeypatch):
    original = Container.build.__func__
    def build(cls, settings):
        c = original(cls, settings)
        async def embed(texts):
            return [[1., .5, .25] for _ in texts]
        c.ollama.embed = embed
        return c
    monkeypatch.setattr(Container, "build", classmethod(build))
    app = create_app(auth_settings(tmp_path))
    with TestClient(app) as client:
        alpha = {"Authorization": "Bearer test-alpha"}
        beta = {"Authorization": "Bearer test-beta"}
        assert client.post("/api/v1/documents", files={"file": ("policy.txt", b"Fictional storm policy.")}, headers=alpha).status_code == 200
        assert client.get("/api/v1/documents", headers=beta).json()["documents"] == []
        source_id = app.state.tenant_containers["alpha"].store.all_chunks()[0].id
        assert client.get("/api/v1/sources/" + source_id, headers=alpha).status_code == 200
        assert client.get("/api/v1/sources/" + source_id, headers=beta).status_code == 404
        assert client.post("/api/v1/agent/memory", headers=alpha, json={"session_id": "shared", "facts": ["Fictional excess is 100."]}).status_code == 200
        assert client.get("/api/v1/agent/memory/shared", headers=beta).json()["facts"] == []


def test_private_course_files_not_static():
    client = TestClient(create_app(Settings(_env_file=None)), client=("127.0.0.1", 9))
    assert client.get("/course/results/ask_traces.jsonl").status_code == 404
    assert client.get("/course/insurance/claims.json").status_code == 404


def test_authenticated_mode_requires_scoped_credentials():
    with pytest.raises(ValueError):
        Settings(_env_file=None, access_mode="authenticated")


def test_tenant_trace_reads_do_not_cross_boundaries(tmp_path):
    from uuid import uuid4
    from app.infrastructure.tracing import TraceLogger
    settings=auth_settings(tmp_path);app=create_app(settings)
    trace_id=str(uuid4())
    suffix=hashlib.sha256(b"alpha").hexdigest()[:24]
    TraceLogger(settings.trace_log_path.parent/(suffix+".jsonl")).write({"trace_id":trace_id,"error":"CLM-2024-88120"})
    with TestClient(app) as client:
        assert client.get('/api/v1/traces/'+trace_id,headers={'Authorization':'Bearer test-alpha'}).status_code==200
        assert client.get('/api/v1/traces/'+trace_id,headers={'Authorization':'Bearer test-beta'}).status_code==404
        assert client.get('/api/v1/traces').status_code==401
