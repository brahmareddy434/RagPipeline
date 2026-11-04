import asyncio
import hashlib
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from time import perf_counter
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import get_settings
from app.dependencies import Container
from app.document_loader import UnsupportedFile
from app.models import (AgentRequest, AgentRunResponse, AnswerResponse, ChatRequest, EvaluationRequest,
                        EvaluationResponse, IngestResponse, InspectRequest, MemoryRequest,
                        ParallelToolRequest, ToolRequest, WorkflowRequest, WorkflowRunResponse)
from app.ollama_client import OllamaUnavailable, call_metrics
from app.prompts import PromptBuilder
from app.trace_logger import TraceLogger

ROOT = Path(__file__).resolve().parents[1]


@asynccontextmanager
async def lifespan(app):
    settings = get_settings()
    app.state.container = Container.build(settings)
    app.state.trace_logger = TraceLogger(settings.trace_log_path)
    try:
        yield
    finally:
        await app.state.container.ollama.close()


app = FastAPI(title=get_settings().app_name, version="2.0.0", lifespan=lifespan)
app.mount("/course", StaticFiles(directory=ROOT / "course", html=True), name="course")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000", "http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])


def container(request):
    return request.app.state.container


@app.exception_handler(OllamaUnavailable)
async def ollama_error(_, exc):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(ValueError)
async def invalid_value(_, exc):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.get("/", response_class=HTMLResponse)
async def home():
    return HTMLResponse((ROOT / "app" / "inspection.html").read_text(encoding="utf-8"))


@app.get("/agent", response_class=HTMLResponse)
async def agent_page():
    """Week 7 demo screen: agent steps and the fixed-workflow comparison, side by side."""
    return HTMLResponse((ROOT / "app" / "agent.html").read_text(encoding="utf-8"))


@app.get("/health")
async def health(request: Request):
    c = container(request)
    models = await c.ollama.health()
    names = [m["name"] for m in models.get("models", [])]
    def installed(name):
        return name in names or name + ":latest" in names
    ready = installed(c.ollama.chat_model) and installed(c.ollama.embed_model)
    return {"status": "ok" if ready else "missing_models", "ollama_models": names,
            "chat_model": c.ollama.chat_model, "embedding_model": c.ollama.embed_model,
            "collection": c.store.collection.name, "chunks": await asyncio.to_thread(c.store.collection.count)}


@app.get("/documents")
async def documents(request: Request):
    rows = await asyncio.to_thread(container(request).store.all_chunks)
    sources = {}
    for row in rows:
        sources[row.source] = sources.get(row.source, 0) + 1
    return {"documents": [{"source": source, "chunks": count} for source, count in sorted(sources.items())]}


@app.delete("/documents/{source}")
async def delete_document(source: str, request: Request):
    deleted = await container(request).store.delete_source(source)
    if not deleted:
        raise HTTPException(404, "No indexed document has that exact filename.")
    return {"source": source, "deleted_chunks": deleted}


@app.delete("/documents")
async def clear_documents(request: Request):
    deleted = await container(request).store.clear()
    return {"deleted_chunks": deleted, "message": "Course index cleared. Upload documents before asking questions."}


@app.get("/sources/{chunk_id}")
async def source(chunk_id: str, request: Request):
    chunk = await asyncio.to_thread(container(request).store.get_chunk, chunk_id)
    if chunk is None:
        raise HTTPException(404, "Source chunk not found. It may have been replaced by a newer document.")
    return chunk


@app.post("/documents", response_model=IngestResponse)
async def upload_document(request: Request, file: UploadFile | None = File(None), files: list[UploadFile] | None = File(None)):
    uploads = ([file] if file else []) + (files or [])
    if not uploads or len(uploads) > 10:
        raise HTTPException(400, "Choose between one and ten files.")
    items = []
    limit = get_settings().max_upload_bytes
    try:
        for upload in uploads:
            if not upload.filename:
                raise HTTPException(400, "Each document needs a filename.")
            if Path(upload.filename).suffix.lower() not in container(request).ingestion.loader.supported:
                raise UnsupportedFile("Use PDF, DOCX, TXT, MD, or HTML.")
            content = await upload.read(limit + 1)
            if len(content) > limit:
                raise HTTPException(413, f"File exceeds {limit} bytes.")
            items.append((upload.filename, content))
        try:
            chunks = await container(request).ingestion.ingest(items)
        except (UnsupportedFile, ValueError, OllamaUnavailable):
            raise
        except Exception as exc:
            logging.exception("Document ingestion failed")
            raise HTTPException(400, "Document could not be parsed or indexed. Check the file and server log.") from exc
        return IngestResponse(files=len(items), chunks=chunks)
    except UnsupportedFile as exc:
        raise HTTPException(415, str(exc)) from exc
    finally:
        for upload in uploads:
            await upload.close()


@app.post("/inspect")
async def inspect(body: InspectRequest, request: Request):
    results, details = await container(request).rag.retriever.inspect(body.question, body.retrieval)
    return {**details, "retrieved": [r.model_dump() for r in results]}


@app.post("/ask", response_model=AnswerResponse)
async def ask(body: ChatRequest, request: Request):
    logger = request.app.state.trace_logger
    trace_id = logger.new_trace_id()
    started = perf_counter()
    metrics = []
    token = call_metrics.set(metrics)
    c = container(request)
    record = {"trace_id": trace_id, "request_id": request.headers.get("X-Request-ID", "")[:128] or logger.new_trace_id(),
              "timestamp": logger.timestamp(), "endpoint": "/ask", "request": body.model_dump(mode="json"),
              "configuration": {"chat_model": c.ollama.chat_model, "embedding_model": c.ollama.embed_model,
                                "collection": c.store.collection.name,
                                "prompt_sha256": hashlib.sha256(PromptBuilder.SYSTEM.encode()).hexdigest()}}
    try:
        record["configuration"]["corpus_sha256"] = await asyncio.to_thread(c.store.fingerprint)
        result = await c.rag.answer(body.question, body.temperature, body.retrieval.k, body.retrieval)
        record.update(status="completed", http_status=200, response=result.model_dump(mode="json"))
        return JSONResponse(result.model_dump(mode="json"), headers={"X-Trace-ID": trace_id})
    except Exception as exc:
        record.update(status="failed", http_status=503 if isinstance(exc, OllamaUnavailable) else 400 if isinstance(exc, ValueError) else 500,
                      error_type=type(exc).__name__, error=str(exc))
        raise
    finally:
        call_metrics.reset(token)
        record.update(latency_ms=round((perf_counter() - started) * 1000, 2), model_calls=metrics)
        try:
            await asyncio.to_thread(logger.write, record)
        except OSError:
            logging.exception("Trace could not be saved")


@app.post("/tools/run")
async def run_tool(body: ToolRequest, request: Request):
    return await container(request).tools.run(body.question)


@app.post("/tools/parallel")
async def parallel_tools(body: ParallelToolRequest, request: Request):
    return {"results": await container(request).tools.parallel(body.questions)}


@app.post("/evaluate", response_model=EvaluationResponse)
async def evaluate(body: EvaluationRequest, request: Request):
    hit_rate, mrr, recall, rows = await container(request).evaluation.evaluate(body.cases, body.k, body.mode)
    return EvaluationResponse(hit_rate_at_k=hit_rate, mrr=mrr, recall_at_k=recall, cases=rows)


# ---------------------------------------------------------------- Week 7: agents


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


@app.post("/agent/run", response_model=AgentRunResponse)
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


@app.post("/workflow/run", response_model=WorkflowRunResponse)
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


@app.post("/agent/race")
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


@app.get("/agent/tools")
async def agent_tools(request: Request):
    """The tool catalogue exactly as the model receives it."""
    registry = container(request).registry
    return {"tools": [{"name": t.name, "description": t.description,
                       "arguments": t.arguments.model_json_schema(), "terminal": t.terminal}
                      for t in registry.tools.values()],
            "catalogue_as_prompted": registry.catalogue()}


@app.get("/agent/memory/{session_id}")
async def read_memory(session_id: str, request: Request):
    return {"session_id": session_id, "facts": await container(request).memory.all_facts(session_id)}


@app.post("/agent/memory")
async def write_memory(body: MemoryRequest, request: Request):
    stored = await container(request).memory.remember(body.session_id, body.facts)
    return {"session_id": body.session_id, "stored": stored}


@app.delete("/agent/memory/{session_id}")
async def clear_memory(session_id: str, request: Request):
    return {"session_id": session_id, "deleted": await container(request).memory.forget(session_id)}
