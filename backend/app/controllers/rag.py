import asyncio
import hashlib
import logging
from time import perf_counter
from fastapi import Request
from fastapi.responses import JSONResponse
from app.schemas import AnswerResponse, ChatRequest, EvaluationRequest, EvaluationResponse, InspectRequest
from app.infrastructure.ollama import OllamaUnavailable, call_metrics
from app.rag.prompts import PromptBuilder

from fastapi import APIRouter
from app.controllers.dependencies import container, trace_logger

router = APIRouter()

@router.post("/inspect")
async def inspect(body: InspectRequest, request: Request):
    results, details = await container(request).rag.retriever.inspect(body.question, body.retrieval)
    return {**details, "retrieved": [r.model_dump() for r in results]}


@router.post("/ask", response_model=AnswerResponse)
async def ask(body: ChatRequest, request: Request):
    logger = trace_logger(request)
    trace_id = logger.new_trace_id()
    started = perf_counter()
    metrics = []
    token = call_metrics.set(metrics)
    c = container(request)
    record = {"trace_id": trace_id, "request_id": request.state.request_id,
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


@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate(body: EvaluationRequest, request: Request):
    hit_rate, mrr, recall, rows = await container(request).evaluation.evaluate(body.cases, body.k, body.mode)
    return EvaluationResponse(hit_rate_at_k=hit_rate, mrr=mrr, recall_at_k=recall, cases=rows)
