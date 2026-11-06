import time
from typing import Literal
from fastapi import APIRouter, Request, HTTPException
from pydantic import Field
from app.schemas import StrictModel,AgentBudget
from app.controllers.dependencies import container
from app.controllers.agents import _trace
from app.agents.claims import task_for
from app.services.claims_evaluation import evaluate
from app.services.claims_reports import benchmark_reports,benchmark_case

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
