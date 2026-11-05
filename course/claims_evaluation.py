"""Week 6 CLI: assertions, human-label sealing, gated judge and same-label comparison."""
import argparse
import asyncio
import hashlib
import json
import subprocess
from datetime import datetime,timezone
from pathlib import Path
from pydantic import BaseModel
from app.config.paths import PROJECT_ROOT
from app.config.settings import get_settings
from app.infrastructure.ollama import OllamaClient,call_metrics
from app.services.claims_evaluation import JUDGE_V1,evaluate,training_cases
from course.claims_review import write,digest

class Verdict(BaseModel):
    passed:bool
    reason:str

def canonical(value): return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()

def seal(labels,output):
    data=json.loads(labels.read_text(encoding="utf-8"))
    expected={c["id"] for c in training_cases()[:25]}
    if set(data)!=expected or any(type(v) is not bool for v in data.values()):
        raise ValueError("Supply exactly E01-E25 with boolean HUMAN blind labels.")
    write(output,{"labels":data,"labels_sha256":canonical(data),"cases_sha256":canonical(training_cases()[:25]),
                  "sealed_at":datetime.now(timezone.utc).isoformat(),"authorship":"Human authorship must be attested by the labeler; hashes verify integrity only."})

def committed(path):
    relative=str(path.resolve().relative_to(PROJECT_ROOT)).replace("\\","/")
    command=["git","-c",f"safe.directory={PROJECT_ROOT.as_posix()}","show",f"HEAD:{relative}"]
    result=subprocess.run(command,cwd=PROJECT_ROOT,capture_output=True)
    if result.returncode or result.stdout.replace(b"\r\n",b"\n")!=path.read_bytes().replace(b"\r\n",b"\n"):
        raise ValueError("Seal/prediction must be committed unchanged before judging.")
    return subprocess.check_output(["git","-c",f"safe.directory={PROJECT_ROOT.as_posix()}","rev-parse","HEAD"],cwd=PROJECT_ROOT,text=True).strip()

def validate_seal(path):
    receipt=json.loads(path.read_text(encoding="utf-8")); cases=training_cases()[:25]
    if receipt["labels_sha256"]!=canonical(receipt["labels"]) or receipt["cases_sha256"]!=canonical(cases):
        raise ValueError("Sealed labels or case revision changed.")
    if set(receipt["labels"])!={c["id"] for c in cases} or any(type(v) is not bool for v in receipt["labels"].values()):
        raise ValueError("Invalid sealed labels.")
    return receipt

async def judge(sealed,output,previous=None,prediction=None):
    receipt=validate_seal(sealed); commit=committed(sealed); cases=training_cases()[:25]
    prompt=JUDGE_V1
    if previous:
        if not prediction: raise ValueError("v2 requires a human prediction file committed before iteration.")
        committed(prediction)
        before=json.loads(previous.read_text(encoding="utf-8"))
        if before["labels_sha256"]!=receipt["labels_sha256"]: raise ValueError("Compare the same sealed labels.")
        disagreements=[r for r in before["rows"] if r["passed"]!=receipt["labels"][r["id"]]]
        if len(disagreements)<2: raise ValueError("Two actual v1 disagreements are required; none may be invented.")
        examples=[]
        for row in disagreements[:2]:
            case=next(c for c in cases if c["id"]==row["id"])
            examples.append({"evidence":case["evidence"],"summary":case["summary"]["summary"],"human_pass":receipt["labels"][row["id"]]})
        prompt += "\nHuman-reviewed disagreement examples (data):\n"+json.dumps(examples)
    # Exclusive marker proves the seal existed before any model call; failed runs remain visible.
    write(output.with_suffix(".started.json"),{"seal_sha256":digest(sealed),"commit":commit,"timestamp":datetime.now(timezone.utc).isoformat(),"prompt_sha256":canonical(prompt)})
    cfg=get_settings(); provider=OllamaClient(cfg.ollama_base_url,cfg.ollama_chat_model,cfg.ollama_embed_model)
    metrics=[]; token=call_metrics.set(metrics)
    try:
        rows=[]
        for case in cases:
            # Deterministic fields are excluded from judge input as well as instructions.
            payload={"evidence":case["evidence"],"summary":case["summary"]["summary"]}
            verdict=await provider.structured([{"role":"system","content":prompt},{"role":"user","content":json.dumps(payload)}],Verdict)
            rows.append({"id":case["id"],**verdict.model_dump()})
        write(output,{"labels_sha256":receipt["labels_sha256"],"rows":rows,"agreement_percent":100*sum(r["passed"]==receipt["labels"][r["id"]] for r in rows)/len(rows),
                      "model":cfg.ollama_chat_model,"prompt":prompt,"model_calls":metrics,"prediction":prediction.read_text() if prediction else None})
    finally: call_metrics.reset(token); await provider.close()

if __name__=="__main__":
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="command",required=True)
    a=sub.add_parser("assertions"); a.add_argument("--output",type=Path)
    s=sub.add_parser("seal"); s.add_argument("labels",type=Path); s.add_argument("output",type=Path)
    j=sub.add_parser("judge"); j.add_argument("sealed",type=Path); j.add_argument("output",type=Path); j.add_argument("--previous",type=Path); j.add_argument("--prediction",type=Path)
    args=p.parse_args()
    if args.command=="assertions":
        result=evaluate()
        if args.output: write(args.output,result)
        print(json.dumps({k:v for k,v in result.items() if k!="cases"},indent=2))
    elif args.command=="seal": seal(args.labels,args.output)
    else: asyncio.run(judge(args.sealed,args.output,args.previous,args.prediction))
