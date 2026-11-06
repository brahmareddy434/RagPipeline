from app.schemas import AgentRequest
from typing import Literal
from pydantic import Field
from app.schemas import StrictModel, AgentBudget

import time
from fastapi import APIRouter,Request
from app.controllers.agents import _trace

router = APIRouter()

class McpDemoRequest(StrictModel):
    task:str=Field(min_length=2,max_length=2000)
    variant:Literal["before","after"]

@router.get("/mcp/demo/tools")
async def demo_tools(variant:Literal["before","after"]):
    from app.services.mcp_host import demo_discovery
    return await demo_discovery(variant)

@router.post("/mcp/demo/run")
async def demo_run(body:McpDemoRequest,request:Request):
    from app.services.mcp_host import demo_config, run_task
    started=time.perf_counter()
    result=await run_task(body.task,config_path=demo_config(body.variant),
        budget=AgentBudget(max_steps=4,max_seconds=180,max_tokens=32000,max_cost_usd=.03))
    result.update(variant=body.variant,task=body.task,
        notice="Fresh MCP host run. The before profile has policy tools only; the after profile adds claims tools. Same host code and prompt.")
    result["trace_id"]=await _trace(request,"/mcp/demo/run",body.model_dump(mode="json"),result,started)
    return result

@router.get("/mcp/tools")
async def mcp_tools():
    """Week 9 catalogue from real tools/list responses (finish is host-local)."""
    from app.infrastructure.mcp.registry import connect, load_config
    from app.services.mcp_host import configured_path
    async with connect(load_config(configured_path())) as registry:
        return {"count": len(registry.tools), "names": list(registry.tools),
                "tools_list_responses": registry.discovery}


@router.post("/mcp/agent/run")
async def mcp_agent_run(body: AgentRequest,request:Request):
    """Same bounded agent with MCP tools; server commands come only from operator config."""
    from app.services.mcp_host import run_task
    started=time.perf_counter()
    result=await run_task(body.task, budget=body.budget)
    result["trace_id"]=await _trace(request,"/mcp/agent/run",body.model_dump(mode="json"),result,started)
    return result
