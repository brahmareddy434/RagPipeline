"""Private trace sampling/replay. Never generates human observations or labels."""
import argparse
import asyncio
import hashlib
import json
import random
from datetime import datetime, timezone
from pathlib import Path

from app.config.paths import PROJECT_ROOT
from app.config.settings import get_settings
from app.infrastructure.ollama import OllamaClient
from app.infrastructure.redaction import redact


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def revision():
    return {str(p.relative_to(PROJECT_ROOT)):digest(p) for folder in ("backend/app","course","frontend/src")
            for p in (PROJECT_ROOT/folder).rglob("*") if p.suffix in {".py",".tsx",".ts",".json",".txt"} and "results" not in p.parts}

def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("x",encoding="utf-8") as stream: json.dump(value,stream,indent=2)

def sample(log,out,seed,count=20):
    if out.exists(): raise ValueError("Use a new review directory; existing evidence must remain unchanged.")
    rng=random.Random(seed); reservoir=[]; total=0; seen=set()
    with log.open(encoding="utf-8") as stream:
        for line in stream:
            record=json.loads(line)
            if record.get("trace_id") in seen: raise ValueError("Duplicate trace ID in input.")
            seen.add(record.get("trace_id")); total+=1
            if len(reservoir)<count: reservoir.append(record)
            else:
                index=rng.randrange(total)
                if index<count: reservoir[index]=record
    if total<count: raise ValueError(f"Need {count} actual traces; only {total} supplied.")
    safe=redact(reservoir,get_settings().redact_names)
    write(out/"sample.json",safe)
    write(out/"observations.json",[{"trace_id":r["trace_id"],"human_observation":""} for r in safe])
    write(out/"freeze.json",{"seed":seed,"population":total,"sample_sha256":digest(out/"sample.json"),
        "input_sha256":digest(log),"source":revision(),"timestamp":datetime.now(timezone.utc).isoformat(),
        "status":"Awaiting human open coding; no categories or fixes generated."})
    return {"population":total,"sampled":count,"seed":seed}

def verify(out):
    frozen=json.loads((out/"freeze.json").read_text(encoding="utf-8"))
    if frozen["source"] != revision(): raise ValueError("Source changed during open coding. Preserve this attempt; start a new frozen phase.")
    if frozen["sample_sha256"] != digest(out/"sample.json"): raise ValueError("Sample changed.")
    rows=json.loads((out/"observations.json").read_text(encoding="utf-8"))
    sampled=json.loads((out/"sample.json").read_text(encoding="utf-8"))
    if [r["trace_id"] for r in rows] != [r["trace_id"] for r in sampled] or any(not r["human_observation"].strip() for r in rows):
        raise ValueError("One human observation is required for every sampled trace, in the frozen order.")
    write(out/"coding_receipt.json",{"observations_sha256":digest(out/"observations.json"),
        "timestamp":datetime.now(timezone.utc).isoformat(),"note":"Integrity/order verified; authorship still requires human review."})

async def replay(trace,output):
    record=json.loads(trace.read_text(encoding="utf-8"))
    if isinstance(record,list): record=random.Random(42).choice(record)
    calls=[m for m in record.get("model_calls",[]) if m.get("endpoint")=="/api/chat" and m.get("request")]
    if not calls: raise ValueError("This trace lacks captured chat payloads; it cannot be replayed from trace alone.")
    settings=get_settings(); client=OllamaClient(settings.ollama_base_url,settings.ollama_chat_model,settings.ollama_embed_model)
    try:
        results=[]
        for call in calls:
            result=await client._request("/api/chat",call["request"])
            results.append({"original":call.get("response"),"replayed":result})
        write(output,redact({"trace_id":record["trace_id"],"calls":results,
             "limitations":["Redacted identities cannot be reconstructed.","Replays saved model requests, not stateful tool side effects.","Model weights/runtime may differ; byte-identical output is not guaranteed."]},settings.redact_names))
    finally: await client.close()

if __name__=="__main__":
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="command",required=True)
    s=sub.add_parser("sample"); s.add_argument("log",type=Path); s.add_argument("output",type=Path); s.add_argument("--seed",type=int,default=42)
    v=sub.add_parser("verify"); v.add_argument("output",type=Path)
    r=sub.add_parser("replay"); r.add_argument("trace",type=Path); r.add_argument("output",type=Path)
    a=p.parse_args()
    if a.command=="sample": print(sample(a.log,a.output,a.seed))
    elif a.command=="verify": verify(a.output)
    else: asyncio.run(replay(a.trace,a.output))
