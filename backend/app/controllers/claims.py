import time
from typing import Literal
from fastapi import APIRouter, Request, HTTPException
from pydantic import Field,model_validator
from app.schemas import StrictModel,AgentBudget
from app.controllers.dependencies import container
from app.controllers.agents import _trace
from app.agents.claims import task_for
from app.services.claims_evaluation import evaluate
from app.services.claims_reports import benchmark_reports,benchmark_case
from course.claims_team_race import run_race,load_latest_race

router=APIRouter()

class DemoRequest(StrictModel):
    task:str=Field(min_length=2,max_length=2000)
    variant:Literal["before","after"]
    injection:bool=False

@router.post("/claims/demo/run")
async def demo_run(body:DemoRequest,request:Request):
    started=time.perf_counter()
    result=await container(request).mentor_demo.run(body.task,body.variant,body.injection,
        AgentBudget(max_steps=6,max_tokens=32000,max_seconds=180,max_cost_usd=.03))
    result["trace_id"]=await _trace(request,"/claims/demo/run",body.model_dump(mode="json"),result,started)
    return result

@router.get("/claims/benchmarks")
async def benchmarks():return benchmark_reports()

@router.get("/claims/benchmarks/{phase}/{approach}/{case_id}")
async def benchmark(phase:str,approach:str,case_id:str):
    record=benchmark_case(phase,approach,case_id)
    if record is None:raise HTTPException(404,"Benchmark case has not been recorded.")
    return record

@router.get("/claims/evaluation")
async def evaluation():
    """Deterministic report over public fictional fixtures; never returns private labels."""
    return evaluate()

class ClaimsRunRequest(StrictModel):
    claim_id:str=Field(pattern=r"^CLM-\d{4}-\d{5}$")
    approach:Literal["agent","workflow","race"]="race"
    budget:AgentBudget=Field(default_factory=lambda:AgentBudget(max_steps=6,max_tokens=32000,max_seconds=180))

class ClaimsTeamRequest(StrictModel):
    claim_id:str=Field(pattern=r"^CLM-\d{4}-\d{5}$")
    arm:Literal["single","team","both","failure"]="both"
    task:str=Field(min_length=2,max_length=2000)

    @model_validator(mode="after")
    def task_names_claim(self):
        if self.claim_id not in self.task:raise ValueError("The question must include the selected fictional claim ID.")
        return self

@router.get("/claims/team/agent-card")
async def claims_agent_card(request:Request):
    """Proposed A2A-style card; this app does not expose the A2A transport."""
    protected=getattr(getattr(request,"state",None),"principal",None) is not None and getattr(getattr(request,"app",None),"state",None) is not None and getattr(request.app.state.settings,"access_mode","local")=="authenticated"
    return {"protocolVersion":"1.0.0","name":"Fictional Claims Triage Team","description":"Manager with narrow coverage and adjuster-note specialists; administrative summaries only.","url":"local://claims-team","version":"1.0.0","capabilities":{"streaming":False,"pushNotifications":False,"stateTransitionHistory":True},"defaultInputModes":["application/json"],"defaultOutputModes":["application/json"],"skills":[{"id":"claims-triage","name":"Fictional claims triage","description":"Summarize status, unresolved issues, and cited clause text without deciding coverage.","tags":["insurance","claims","fictional-fixture"],"examples":["Summarize status and unresolved issues for CLM-2026-10001."],"inputModes":["application/json"],"outputModes":["application/json"]}],"securitySchemes":{"bearerAuth":{"type":"http","scheme":"bearer"}} if protected else {},"security":[{"bearerAuth":[]}] if protected else []}

@router.post("/claims/team/run")
async def claims_team_run(body:ClaimsTeamRequest,request:Request):
    c=container(request);c.claims_registry.repository.get(body.claim_id)
    budget=AgentBudget(max_steps=6,max_tokens=64000,max_seconds=300,max_cost_usd=.08)
    result={"claim_id":body.claim_id,"provenance":"fictional training fixture","arm":body.arm}
    if body.arm in {"single","both"}:
        result["single"]=(await c.claims_agent.run(body.task,budget=budget)).model_dump(mode="json")
    if body.arm in {"team","both","failure"}:
        run=await c.claims_team.run(body.claim_id,budget=budget,task=body.task,fail_coverage=body.arm=="failure")
        result["team"]=run.model_dump(mode="json")
        result["task_state"]="failed" if run.stop_reason=="worker_error" else "completed" if run.completed else "failed"
    return result

@router.post("/claims/team/race")
async def claims_team_race(request:Request):
    """Run both arms on the frozen provisional ten-case cohort and save artifacts."""
    return await run_race(container(request))

@router.get("/claims/team/race/latest")
async def claims_team_latest_race():
    report=load_latest_race()
    if report is None:raise HTTPException(404,"No saved claims-team race is available yet.")
    return report

@router.get("/claims/fixtures")
async def fixtures(request:Request):
    registry=container(request).claims_registry
    return {"provenance":"Fictional read-only training records shared by all demo tenants.",
            "claims":[{"claim_id":r.claim_id,"status":r.status.value} for r in registry.repository.records.values()],
            "tools":[{"name":t.name,"description":t.description,"arguments":t.arguments.model_json_schema()} for t in registry.tools.values()]}

@router.post("/claims/run")
async def run_claim(body:ClaimsRunRequest,request:Request):
    c=container(request); c.claims_registry.repository.get(body.claim_id)
    started=time.perf_counter();result={"claim_id":body.claim_id,"provenance":"fictional training fixture"}
    if body.approach in {"agent","race"}:result["agent"]=(await c.claims_agent.run(task_for(body.claim_id),budget=body.budget)).model_dump(mode="json")
    if body.approach in {"workflow","race"}:result["workflow"]=(await c.claims_workflow.run(body.claim_id,body.budget)).model_dump(mode="json")
    result["trace_id"]=await _trace(request,"/claims/run",body.model_dump(mode="json"),result,started)
    return result
