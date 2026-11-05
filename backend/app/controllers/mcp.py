from app.schemas import AgentRequest

import time
from fastapi import APIRouter,Request
from app.controllers.agents import _trace

router = APIRouter()

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
