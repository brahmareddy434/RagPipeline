"""Isolated, live-Ollama Week 3/4 experiments over explicitly fictional inputs."""
import argparse
import asyncio
import hashlib
import json
import platform
import statistics
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from app.bootstrap import Container
from app.config.paths import PROJECT_ROOT
from app.config.settings import get_settings
from app.schemas import RetrievalOptions

CORPUS = PROJECT_ROOT / "course/insurance/claims-policy-2026.txt"
QUESTIONS = PROJECT_ROOT / "course/insurance/retrieval-questions.json"


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


async def measure(c, cases, mode):
    rows = []
    for case in cases:
        started = time.perf_counter()
        found, details = await c.rag.retriever.inspect(case["question"], RetrievalOptions(mode=mode, k=3))
        hit = bool(set(case["correct_chunk_ids"]) & {r.id for r in found})
        rows.append({**case, "hit_at_3": hit, "latency_ms": round((time.perf_counter()-started)*1000, 2),
                     "label": "hit" if hit else "R" if case["correct_chunk_ids"] else "Not-In-Corpus",
                     "inspection": details, "retrieved": [r.model_dump() for r in found]})
    return {"mode": mode, "hit_rate_at_3": sum(r["hit_at_3"] for r in rows)/len(rows),
            "p50_latency_ms": statistics.median(r["latency_ms"] for r in rows), "cases": rows}


async def run(kind, output):
    out = output / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    fixture = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    settings = get_settings()
    manifest = {"provenance": fixture["provenance"], "timestamp": datetime.now(timezone.utc).isoformat(),
                "model": settings.ollama_chat_model, "embedding_model": settings.ollama_embed_model,
                "python": platform.python_version(), "platform": platform.platform(),
                "corpus_sha256": hashlib.sha256(CORPUS.read_bytes()).hexdigest(),
                "questions_sha256": hashlib.sha256(QUESTIONS.read_bytes()).hexdigest(),
                "source_sha256": {p: hashlib.sha256((PROJECT_ROOT/p).read_bytes()).hexdigest() for p in
                    ["backend/app/rag/retrieval.py", "backend/app/rag/chunking.py", "course/claims_retrieval.py"]},
                "cache": "Document embeddings precomputed; all query embeddings warmed before each arm; sequential single runner.",
                "generation_labels": "Retrieval-only R/missing labels; G requires inspecting an actual generated answer."}
    save(out/"manifest.json",manifest)
    for size in ([400,900] if kind == "chunking" else [600]):
        with tempfile.TemporaryDirectory(prefix="claims-retrieval-") as tmp:
            cfg = settings.model_copy(update={"chroma_path": Path(tmp), "collection_name":"claims_lab",
                       "memory_collection_name":"lab_memory", "chunk_size":size,"chunk_overlap":80})
            c = Container.build(cfg)
            try:
                started=time.perf_counter()
                count=await c.ingestion.ingest([(CORPUS.name,CORPUS.read_bytes())])
                indexing_ms=round((time.perf_counter()-started)*1000,2)
                chunks=c.store.all_chunks()
                cases=[{**case,"correct_chunk_ids":[r.id for r in chunks if case["needle"] in r.text]} for case in fixture["cases"]]
                if not all(case["correct_chunk_ids"] for case in cases):
                    raise ValueError("A golden quote crossed a chunk boundary; inspect corpus/chunking before freezing the benchmark.")
                save(out/f"golden-{size}.json",cases)
                for case in cases:
                    await c.ollama.embed([case["question"]])
                baseline=await measure(c,cases,"semantic")
                save(out/f"baseline-{size}.json", {"chunks":count,"indexing_ms":indexing_ms,**baseline})
                if kind == "retrieval":
                    after=await measure(c,cases,"hybrid")
                    save(out/"after.json",after)
                    fixed=[b["id"] for b,a in zip(baseline["cases"],after["cases"]) if not b["hit_at_3"] and a["hit_at_3"]]
                    regressed=[b["id"] for b,a in zip(baseline["cases"],after["cases"]) if b["hit_at_3"] and not a["hit_at_3"]]
                    save(out/"comparison.json",{"only_change":"retrieval.mode: semantic -> hybrid (BM25 + RRF k=60)",
                        "before":{k:baseline[k] for k in ("hit_rate_at_3","p50_latency_ms")},
                        "after":{k:after[k] for k in ("hit_rate_at_3","p50_latency_ms")},"fixed":fixed,"regressed":regressed})
                else:
                    answers=[]
                    for question in [cases[4]["question"],"What is the policy coverage for a lunar spacecraft?"]:
                        result=await c.rag.answer(question,0,4,RetrievalOptions(k=4))
                        answers.append({"question":question,"response":result.model_dump(mode="json")})
                    save(out/f"answers-{size}.json",answers)
                print(f"{size}: {count} chunks, hit@3={baseline['hit_rate_at_3']:.3f}, p50={baseline['p50_latency_ms']:.2f}ms",flush=True)
            finally:
                await c.ollama.close()
                # Chroma owns file handles until process exit on Windows. Stop this disposable instance.
                c.store.client._system.stop()
    print(f"Evidence: {out}",flush=True)


if __name__ == "__main__":
    p=argparse.ArgumentParser(); p.add_argument("kind",choices=["chunking","retrieval"])
    p.add_argument("--output",type=Path,default=PROJECT_ROOT/"docs/demos/evidence/claims-retrieval")
    a=p.parse_args(); asyncio.run(run(a.kind,a.output))
