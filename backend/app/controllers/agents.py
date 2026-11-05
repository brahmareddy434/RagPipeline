import asyncio
import logging
from time import perf_counter
from fastapi import Request
from fastapi.responses import JSONResponse
from app.schemas import AgentRequest, AgentRunResponse, MemoryRequest, WorkflowRequest, WorkflowRunResponse

from fastapi import APIRouter
from app.controllers.dependencies import container

router = APIRouter()

async def _trace(request, endpoint, body, result, started, error=None):
    """Agent and workflow runs are traces too: same log, same Week 5 analysis tooling."""
    logger = request.app.state.trace_logger
    record = {"trace_id": logger.new_trace_id(), "timestamp": logger.timestamp(), "endpoint": endpoint,
              "request": body, "latency_ms": round((perf_counter() - started) * 1000, 2)}
    record.update({"status": "failed", "error": str(error), "error_type": type(error).__name__}
                  if error else {"status": "completed", "response": result})
    try:
        # Off the event loop, matching /ask: an agent trace carries every step and is not tiny.
        await asyncio.to_thread(logger.write, record)
    except OSError:
        logging.exception("Trace could not be saved")
    return record["trace_id"]


@router.post("/agent/run", response_model=AgentRunResponse)
async def agent_run(body: AgentRequest, request: Request):
    """Run the ReAct loop. Every step, budget and stop reason is in the response."""
    started = perf_counter()
    try:
        result = await container(request).agent.run(body.task, body.session_id, body.budget)
    except Exception as exc:
        await _trace(request, "/agent/run", body.model_dump(mode="json"), None, started, exc)
        raise
    payload = result.model_dump(mode="json")
    trace_id = await _trace(request, "/agent/run", body.model_dump(mode="json"), payload, started)
    return JSONResponse(payload, headers={"X-Trace-ID": trace_id})


@router.post("/workflow/run", response_model=WorkflowRunResponse)
async def workflow_run(body: WorkflowRequest, request: Request):
    """Run the same task as a fixed sequence, for the speed/cost/reliability comparison."""
    started = perf_counter()
    try:
        result = await container(request).workflow.run(body.task)
    except Exception as exc:
        await _trace(request, "/workflow/run", body.model_dump(mode="json"), None, started, exc)
        raise
    payload = result.model_dump(mode="json")
    trace_id = await _trace(request, "/workflow/run", body.model_dump(mode="json"), payload, started)
    return JSONResponse(payload, headers={"X-Trace-ID": trace_id})


@router.post("/agent/race")
async def agent_race(body: AgentRequest, request: Request):
    """Run both on one task and return the side-by-side numbers. Sequential, not concurrent,
    so neither contends with the other for the single local Ollama runner."""
    c = container(request)
    agent = await c.agent.run(body.task, body.session_id, body.budget)
    workflow = await c.workflow.run(body.task)
    def row(run, kind):
        usage = run.usage
        return {"approach": kind, "latency_ms": usage.get("latency_ms"), "model_calls": usage.get("model_calls"),
                "total_tokens": usage.get("total_tokens"), "steps": usage.get("steps"),
                "abstained": run.abstained, "citations": len(run.citations), "answer": run.answer}
    return {"task": body.task, "agent": row(agent, "agent"), "workflow": row(workflow, "fixed_workflow"),
            "agent_run": agent.model_dump(mode="json"), "workflow_run": workflow.model_dump(mode="json"),
            "note": "One task is an anecdote. Run course/race.py over the scenario set for real numbers."}


@router.get("/agent/tools")
async def agent_tools(request: Request):
    """The tool catalogue exactly as the model receives it."""
    registry = container(request).registry
    return {"tools": [{"name": t.name, "description": t.description,
                       "arguments": t.arguments.model_json_schema(), "terminal": t.terminal}
                      for t in registry.tools.values()],
            "catalogue_as_prompted": registry.catalogue()}


@router.get("/agent/memory/{session_id}")
async def read_memory(session_id: str, request: Request):
    return {"session_id": session_id, "facts": await container(request).memory.all_facts(session_id)}


@router.post("/agent/memory")
async def write_memory(body: MemoryRequest, request: Request):
    stored = await container(request).memory.remember(body.session_id, body.facts)
    return {"session_id": body.session_id, "stored": stored}


@router.delete("/agent/memory/{session_id}")
async def clear_memory(session_id: str, request: Request):
    return {"session_id": session_id, "deleted": await container(request).memory.forget(session_id)}
