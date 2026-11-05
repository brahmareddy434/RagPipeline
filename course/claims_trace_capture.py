"""Capture actual fictional claims RAG runs in a disposable store."""
import argparse
import asyncio
import hashlib
import json
import tempfile
from pathlib import Path
from app.bootstrap import Container
from app.config.paths import PROJECT_ROOT
from app.config.settings import get_settings
from app.infrastructure.ollama import call_metrics
from app.infrastructure.tracing import TraceLogger
from course.claims_retrieval import CORPUS, QUESTIONS

async def capture(output,count):
    if output.exists(): raise ValueError("Choose a new output path to preserve previous traces.")
    cfg=get_settings(); cases=json.loads(QUESTIONS.read_text())["cases"]
    with tempfile.TemporaryDirectory(prefix="claims-traces-") as tmp:
        c=Container.build(cfg.model_copy(update={"chroma_path":Path(tmp),"collection_name":"trace_documents","memory_collection_name":"trace_memory"}))
        logger=TraceLogger(output,cfg.redact_names)
        try:
            await c.ingestion.ingest([(CORPUS.name,CORPUS.read_bytes())])
            for i in range(count):
                question=cases[i%len(cases)]["question"]; metrics=[]; token=call_metrics.set(metrics)
                try:
                    answer=await c.rag.answer(question,0,4)
                    logger.write({"trace_id":logger.new_trace_id(),"timestamp":logger.timestamp(),"endpoint":"/ask",
                        "provenance":"Actual local Ollama run over assistant-authored fictional claims corpus.",
                        "status":"completed","request":{"question":question},"response":answer.model_dump(mode="json"),
                        "configuration":{"corpus_sha256":hashlib.sha256(CORPUS.read_bytes()).hexdigest(),"model":cfg.ollama_chat_model},"model_calls":metrics})
                    print(f"Captured {i+1}/{count}",flush=True)
                finally: call_metrics.reset(token)
        finally:
            await c.ollama.close(); c.store.client._system.stop()

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("output",type=Path); p.add_argument("--count",type=int,default=20)
    a=p.parse_args()
    if not 1<=a.count<=100: p.error("count must be 1..100")
    asyncio.run(capture(a.output,a.count))
