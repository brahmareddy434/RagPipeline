"""Deterministic outcome proxies and independent path metrics for fictional claims."""
from collections import Counter
from itertools import permutations
import statistics

TERMS={"10001":"estimate","10002":"wear","10003":"flood","10004":"pre-existing","10005":"report",
       "10006":"plumber","10007":"glass","10008":"coverage","10009":"deliberate","10010":"edition"}

def expectations(repository):
    cases=[]
    for record in repository.records.values():
        base=[("get_claim_record",record.claim_id),("get_adjuster_notes",record.claim_id)]
        paths=[]
        for prefix in (base,list(reversed(base))):
            for clauses in permutations(record.required_clauses):
                paths.append(prefix+[("read_policy_clause",c) for c in clauses])
        cases.append({"claim_id":record.claim_id,"status":record.status.value,"term":TERMS[record.claim_id[-5:]],
                      "required_clauses":record.required_clauses,"allowed_paths":paths})
    return cases

def assess(run,case,registry):
    steps=run.steps;path=[];real=[];choices=[]
    for step in steps:
        name=step.get("tool");args=step.get("arguments",{});valid=True
        try:
            parsed=registry.validate(name,args)
            if name=="read_policy_clause":registry.repository.clause(parsed.clause_id)
            else:
                registry.repository.get(parsed.claim_id)
                if parsed.claim_id!=case["claim_id"]:valid=False
        except Exception:valid=False
        real.append(valid and step.get("ok",False))
        argument=args.get("clause_id",args.get("claim_id",""));path.append((name,argument))
        choices.append(name in registry.tools and (name!="read_policy_clause" or argument in case["required_clauses"]))
    allowed=[[tuple(s) for s in p] for p in case["allowed_paths"]]
    trajectory=path in allowed and all(real)
    normalized=run.answer.lower().replace('_',' ')
    status_ok=case["status"].replace('_',' ') in normalized
    term_ok=case["term"] in normalized
    required_text={"10001":["estimate"],"10002":["wear"],"10003":["flood"],"10004":["pre-existing"],
                   "10005":["report"],"10006":["plumber"],"10007":["glass"],"10008":["closed"],
                   "10009":["deliberate"],"10010":["edition"]}[case["claim_id"][-5:]]
    outcome=not run.abstained and status_ok and term_ok and all(word in normalized for word in required_text)
    mode=("invalid_arguments" if not all(real) else "repeated_calls" if len(path)!=len(set(path)) else
          "missing_clause" if not set(case["required_clauses"]).issubset({a for n,a in path if n=="read_policy_clause"}) else
          "wrong_path" if not trajectory else "abstention" if run.abstained else "outcome_miss" if not outcome else "pass")
    minimum=min(map(len,allowed))
    return {"outcome_pass":outcome,"trajectory_pass":trajectory,"mode":mode,
            "outcome_checks":{"status":status_ok,"note_detail":term_ok,"policy_clause_path":all(("read_policy_clause",c) in path for c in case["required_clauses"])},
            "tool_choice_accuracy":sum(choices)/len(choices) if choices else 0,
            "argument_validity":sum(real)/len(real) if real else 0,
            "step_efficiency":min(1,minimum/len(path)) if path else 0,"path":path}

def summarize(rows):
    count=len(rows)
    return {"cases":count,"outcome_pass_rate":sum(r["assessment"]["outcome_pass"] for r in rows)/count,
            "trajectory_pass_rate":sum(r["assessment"]["trajectory_pass"] for r in rows)/count,
            "outcome_minus_trajectory_gap":sum(int(r["assessment"]["outcome_pass"])-int(r["assessment"]["trajectory_pass"]) for r in rows)/count,
            "p50_latency_ms":statistics.median(r["run"]["usage"]["latency_ms"] for r in rows),
            "total_tokens":sum(r["run"]["usage"]["total_tokens"] for r in rows),
            "mean_cost_per_claim_usd":statistics.mean(r["run"]["usage"]["cost_usd"] for r in rows),
            "cost_p50_usd":statistics.median(r["run"]["usage"]["cost_usd"] for r in rows),
            "cost_max_usd":max(r["run"]["usage"]["cost_usd"] for r in rows),
            **{k:statistics.mean(r["assessment"][k] for r in rows) for k in ("tool_choice_accuracy","argument_validity","step_efficiency")},
            "modes":dict(Counter(r["assessment"]["mode"] for r in rows)),
            "right_answer_wrong_path":[r["case_id"] for r in rows if r["assessment"]["outcome_pass"] and not r["assessment"]["trajectory_pass"]]}
