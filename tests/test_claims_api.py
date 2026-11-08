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


def test_week10_api_pairs_exact_user_task_and_agent_card_discloses_auth_scheme(monkeypatch):
    from app.agents.claims import task_for
    from app.agents.claims_team import ClaimsTeam
    calls=[]
    class Repository:
        def get(self,claim_id):return object()
    class Runner:
        async def run(self,task,budget,**kwargs):
            calls.append((task,budget,kwargs))
            return AgentRunResponse(task=task,answer="Under review.",stop_reason="finished")
    class TeamRunner:
        async def run(self,claim_id,budget,*,task,fail_coverage=False):
            calls.append((task,budget,{"claim_id":claim_id,"fail_coverage":fail_coverage}))
            return AgentRunResponse(task=task,answer="Under review.",stop_reason="finished")
    fake=SimpleNamespace(claims_registry=SimpleNamespace(repository=Repository()),claims_agent=Runner(),claims_team=TeamRunner())
    monkeypatch.setattr(claims,"container",lambda request:fake)
    app=FastAPI();app.include_router(claims.router)
    task=task_for("CLM-2026-10001")
    with TestClient(app) as client:
        pair=client.post("/claims/team/run",json={"claim_id":"CLM-2026-10001","task":task,"arm":"both"})
        card=client.get("/claims/team/agent-card")
        invalid=client.post("/claims/team/run",json={"claim_id":"CLM-2026-10001","task":"Tell me about another claim","arm":"failure"})
    assert pair.status_code==200 and calls[0][0]==calls[1][0]==task and calls[0][1] is calls[1][1]
    assert card.status_code==200 and card.json()["defaultInputModes"]==["application/json"]
    assert card.json()["securitySchemes"]=={}
    assert invalid.status_code==422


def test_week10_latest_race_artifact_endpoint_returns_saved_report_or_404(monkeypatch):
    monkeypatch.setattr(claims,"load_latest_race",lambda:{"generated_at_utc":"fixture","artifacts":{"run_id":"reviewed-run"}})
    app=FastAPI();app.include_router(claims.router)
    with TestClient(app) as client:
        response=client.get("/claims/team/race/latest")
    assert response.status_code==200 and response.json()["artifacts"]["run_id"]=="reviewed-run"
    monkeypatch.setattr(claims,"load_latest_race",lambda:None)
    with TestClient(app) as client:
        missing=client.get("/claims/team/race/latest")
    assert missing.status_code==404
