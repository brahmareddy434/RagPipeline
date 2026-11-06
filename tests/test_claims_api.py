from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.controllers import claims
from app.schemas import AgentRunResponse


def test_claims_race_contract_uses_same_claim_and_returns_both_runs(monkeypatch):
    calls=[]

    class Repository:
        def get(self,claim_id):
            assert claim_id=="CLM-2026-10001"
            return object()

    class Runner:
        async def run(self,task,budget):
            calls.append((task,budget))
            return AgentRunResponse(task=task,answer="Under review.",stop_reason="finished")

    fake=SimpleNamespace(claims_registry=SimpleNamespace(repository=Repository()),claims_agent=Runner(),claims_workflow=Runner())
    monkeypatch.setattr(claims,"container",lambda request:fake)

    async def trace(*args,**kwargs):return "trace-fixture"
    monkeypatch.setattr(claims,"_trace",trace)
    app=FastAPI();app.include_router(claims.router)
    with TestClient(app) as client:
        response=client.post("/claims/run",json={"claim_id":"CLM-2026-10001","approach":"race"})
        assert response.status_code==200
        body=response.json()
        assert body["claim_id"]=="CLM-2026-10001" and body["trace_id"]=="trace-fixture"
        assert body["agent"]["answer"]==body["workflow"]["answer"]=="Under review."
        assert len(calls)==2
        assert "CLM-2026-10001" in calls[0][0]
        assert calls[1][0]=="CLM-2026-10001"
        assert calls[0][1]==calls[1][1]


def test_claims_run_rejects_malformed_claim_id_before_dispatch():
    app=FastAPI();app.include_router(claims.router)
    with TestClient(app) as client:
        response=client.post("/claims/run",json={"claim_id":"invented","approach":"agent"})
    assert response.status_code==422
