"""Freeze paired ten-claim inputs and apply the existing Week 8 judge to both arms."""
import hashlib
import json
import math
import statistics
import re
from datetime import datetime, timezone
from pathlib import Path

from app.agents.claims import task_for
from app.config.paths import PROJECT_ROOT
from course.claims_trajectories import assess, expectations, summarize
from app.schemas import AgentBudget


def _digest(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(encoded).hexdigest()


def freeze_cases(repository, records=None):
    selected = list(records if records is not None else repository.records.values())
    if len(selected) != 10:
        raise ValueError("Week 10 paired race requires exactly ten claims.")
    ids = [record.claim_id for record in selected]
    if len(set(ids)) != len(ids):
        raise ValueError("Week 10 cohort contains duplicate claim IDs.")
    if any(repository.records.get(claim_id) is None for claim_id in ids):
        raise ValueError("Week 10 cohort contains a claim outside the reviewed fixture.")
    expected = expectations(repository)
    by_id = {case["claim_id"]: case for case in expected}
    cases = []
    for index, record in enumerate(selected, 1):
        base = by_id.get(record.claim_id)
        if base is None:
            raise ValueError("Week 10 cohort does not match the reviewed expected-path set.")
        cases.append({"case_id": f"C{index:02}", "task": task_for(record.claim_id), **base})
    judge_hash = hashlib.sha256((PROJECT_ROOT / "course/claims_trajectories.py").read_bytes()).hexdigest()
    corpus_hash = hashlib.sha256((PROJECT_ROOT / "course/insurance/triage-claims.json").read_bytes()).hexdigest()
    return cases, {
        "case_count": len(cases), "case_ids": [c["case_id"] for c in cases],
        "claim_ids": ids, "cohort_sha256": _digest(cases), "fixture_sha256": corpus_hash,
        "judge_sha256": judge_hash, "exact_week6_cohort": False,
        "cohort_provenance": "Existing ten fictional Week-7/8 claims and predeclared trajectory cases; provisional Week 10 substitute, not the missing Week-6 claims cohort.",
        "judge": "course.claims_trajectories.assess (unchanged Week-8 deterministic outcome and trajectory checks)",
    }


def _arm_rows(rows, cases, registry, label, *, apply_judge=True):
    if len(rows) != len(cases):
        raise ValueError(f"{label} arm must contain exactly ten paired cases.")
    validated = []
    seen = set()
    for row, case in zip(rows, cases, strict=True):
        if row.get("case_id") != case["case_id"] or row.get("task") != case["task"]:
            raise ValueError(f"{label} arm cases and queries must be identical to the frozen cohort.")
        if case["case_id"] in seen:
            raise ValueError(f"{label} arm contains duplicate cases.")
        seen.add(case["case_id"])
        run = row["run"]
        if run.task != case["task"]:
            raise ValueError(f"{label} arm run query differs from the frozen cohort.")
        validated.append((case, run))
    return [{"case_id": case["case_id"], "claim_id": case["claim_id"],
             "assessment": assess(run, case, registry) if apply_judge else None, "run": run}
            for case, run in validated]


def judge_arms(single_rows, team_rows, cases, registry):
    if len(cases) != 10 or len({case["case_id"] for case in cases}) != 10:
        raise ValueError("Paired judge requires the same ten unique frozen cases.")
    if len(single_rows) != 10 or len(team_rows) != 10:
        raise ValueError("Both paired arms must contain all ten cases before judging.")
    # Validate the full pair before invoking the judge on either arm.
    _arm_rows(single_rows, cases, registry, "Single", apply_judge=False)
    _arm_rows(team_rows, cases, registry, "Team", apply_judge=False)
    single = _arm_rows(single_rows, cases, registry, "Single")
    team = _arm_rows(team_rows, cases, registry, "Team")
    if [(r["case_id"], r["run"].task) for r in single] != [(r["case_id"], r["run"].task) for r in team]:
        raise ValueError("Single and team arms must be judged on identical case IDs and queries.")
    return {"case_ids": [case["case_id"] for case in cases], "single": single, "team": team,
            "judge": "course.claims_trajectories.assess"}


def _percentile99(values):
    ordered=sorted(values)
    return ordered[max(0,math.ceil(.99*len(ordered))-1)]


def load_latest_race():
    """Return the latest reviewed race artifacts using a fixed, local path allowlist."""
    root=PROJECT_ROOT/"docs/demos/evidence/claims-team-race"
    if not root.is_dir():
        return None
    runs=sorted((p for p in root.iterdir() if p.is_dir() and re.fullmatch(r"provisional-week7-8-\d{8}T\d{6}-\d{6}Z",p.name)),key=lambda p:p.name)
    if not runs:
        return None
    latest=runs[-1]
    report=json.loads((latest/"race.json").read_text(encoding="utf-8"))
    report["artifacts"]={name:(latest/name).read_text(encoding="utf-8") for name in ("race_table.md","handoffs.log","failure_case.md","verdict.md")}
    report["artifacts"]["run_id"]=latest.name
    return report


async def run_race(container):
    """Run the frozen pair once and write the five requested, reviewable artifacts."""
    cases,manifest=freeze_cases(container.claims_registry.repository)
    budget=AgentBudget(max_steps=6,max_tokens=64000,max_seconds=300,max_cost_usd=.08)
    single_rows=[];team_rows=[];all_handoffs=[]
    for index,case in enumerate(cases):
        claim_id=case["claim_id"]
        if index%2==0:
            single=await container.claims_agent.run(case["task"],budget=budget)
            team=await container.claims_team.run(claim_id,budget=budget,task=case["task"])
        else:
            team=await container.claims_team.run(claim_id,budget=budget,task=case["task"])
            single=await container.claims_agent.run(case["task"],budget=budget)
        single_rows.append({"case_id":case["case_id"],"task":case["task"],"run":single})
        team_rows.append({"case_id":case["case_id"],"task":case["task"],"run":team})
        for call in team.usage["provider_calls"]:
            pt=call.get("prompt_eval_count") or 0;ct=call.get("eval_count") or 0
            all_handoffs.append({"case_id":case["case_id"],"claim_id":claim_id,
                "handoff":call.get("call_group","unattributed"),"prompt_tokens":pt,"completion_tokens":ct,
                "total_tokens":pt+ct,"status":call.get("status","completed"),"usage_status":call.get("usage_status","unknown")})
        all_handoffs.append({"case_id":case["case_id"],"claim_id":claim_id,"handoff":"manager_synthesis",
            "prompt_tokens":0,"completion_tokens":0,"total_tokens":0,"status":"deterministic verified-quote synthesis","usage_status":"no model call"})
    paired=judge_arms(single_rows,team_rows,cases,container.claims_registry)
    single_sum=summarize([{**r,"run":r["run"].model_dump(mode="json")} for r in paired["single"]])
    team_sum=summarize([{**r,"run":r["run"].model_dump(mode="json")} for r in paired["team"]])
    for summary,rows in ((single_sum,paired["single"]),(team_sum,paired["team"])):
        latencies=[r["run"].usage["latency_ms"] for r in rows]
        costs=[r["run"].usage["cost_usd"] for r in rows]
        summary["p50_latency_ms"]=statistics.median(latencies)
        summary["p99_latency_ms"]=_percentile99(latencies)
        summary["total_tokens"]=sum(r["run"].usage["total_tokens"] for r in rows)
        summary["cost_per_claim_usd"]=statistics.mean(costs)
    single_total=single_sum["total_tokens"];team_total=team_sum["total_tokens"]
    groups={}
    for event in all_handoffs:
        group=event["handoff"];groups[group]=groups.get(group,0)+event["total_tokens"]
    dominant=max(groups,key=groups.get) if groups else "no recorded hand-offs"
    share=groups.get(dominant,0)/team_total*100 if team_total else 0
    failure=await container.claims_team.run(cases[0]["claim_id"],budget=budget,fail_coverage=True)
    report={"generated_at_utc":datetime.now(timezone.utc).isoformat(),"model":container.ollama.chat_model,
        "budget":budget.model_dump(mode="json"),"cost_basis":"Reference estimate from app.schemas.usd_cost; not a provider invoice.","manifest":manifest,
        "same_ten_case_ids":manifest["case_ids"],"execution_order":"Alternated single-first/team-first by paired case to reduce fixed order bias.","judge":paired["judge"],"single":single_sum,"team":team_sum,
        "context_resend_multiplier":round(team_total/single_total,1) if single_total else None,
        "dominant_handoff":dominant,"dominant_handoff_tokens":groups.get(dominant,0),
        "dominant_handoff_share_percent":round(share,1),"failure_case_id":cases[0]["case_id"],
        "failure_stop_reason":failure.stop_reason,"failure_answer":failure.answer,
        "failure_record":failure.usage.get("worker_failures",[])}
    # The provisional run is evidence, but is intentionally not misrepresented as the absent Week-6 claims cohort.
    run_id=datetime.now(timezone.utc).strftime("provisional-week7-8-%Y%m%dT%H%M%S-%fZ")
    root=PROJECT_ROOT/"docs/demos/evidence/claims-team-race"/run_id
    root.mkdir(parents=True,exist_ok=True)
    race_table=_race_table(report)
    (root/"race_table.md").write_text(race_table,encoding="utf-8")
    with (root/"handoffs.log").open("w",encoding="utf-8") as stream:
        stream.write("case_id | claim_id | handoff | prompt_tokens | completion_tokens | total_tokens | status | usage_status\n")
        for event in all_handoffs:stream.write(" | ".join(str(event[k]) for k in ("case_id","claim_id","handoff","prompt_tokens","completion_tokens","total_tokens","status","usage_status"))+"\n")
        stream.write(f"\nContext re-send multiplier: {report['context_resend_multiplier']}x (team/single tokens). Dominant hand-off: {dominant}, {groups.get(dominant,0)} tokens, {share:.1f}% of team tokens.\n")
    failure_calls="; ".join(f"{m.get('call_group','unattributed')}={((m.get('prompt_eval_count') or 0)+(m.get('eval_count') or 0))} tokens" for m in failure.usage.get("provider_calls",[]))
    failure_text=f"Injected in-process HTTP 500 from coverage/exclusions worker on {cases[0]['case_id']} ({cases[0]['claim_id']}).\nObserved: stop_reason={failure.stop_reason}; abstained={failure.abstained}; answer={failure.answer}\nBehavior: no retry; safe abstention/partial response; no unsupported coverage assertion.\nRecorded worker failure: {failure.usage.get('worker_failures',[])}\nFailure-call token accounting: {failure_calls}\nCoverage worker hand-off: 0 provider tokens (injected 500 before worker model call).\n"
    verdict_text=_verdict(report)
    (root/"failure_case.md").write_text(failure_text,encoding="utf-8")
    (root/"verdict.md").write_text(verdict_text,encoding="utf-8")
    (root/"race.json").write_text(json.dumps(report,indent=2,default=lambda x:x.model_dump(mode="json") if hasattr(x,"model_dump") else str(x)),encoding="utf-8")
    report["artifacts"]={"race_table.md":race_table,"handoffs.log":(root/"handoffs.log").read_text(encoding="utf-8"),"failure_case.md":failure_text,"verdict.md":verdict_text,"run_id":run_id}
    return report


def _race_table(report):
    lines=["# Week 10 claims squad race (provisional cohort)","",
        "Cases: "+", ".join(report["same_ten_case_ids"]),"",
        "WARNING: the required Week-6 claims question cohort is absent from this repository. This run uses the existing ten Week-7/8 trajectory fixtures and is not a rubric-complete Week-6 comparison.","",
        "| Metric | Single agent | Manager + specialists |","|---|---:|---:|"]
    for label,key,fmt in (("Pass rate (deterministic outcome proxy)","outcome_pass_rate",lambda x:f"{x:.0%}"),("p50 latency","p50_latency_ms",lambda x:f"{x:.0f} ms"),("p99 latency","p99_latency_ms",lambda x:f"{x:.0f} ms"),("Total tokens","total_tokens",lambda x:str(x)),("Mean cost per claim (estimated)","cost_per_claim_usd",lambda x:f"${x:.6f}")):
        lines.append(f"| {label} | {fmt(report['single'][key])} | {fmt(report['team'][key])} |")
    lines.extend(["",f"Model: `{report['model']}`; server-owned paired budget: `{report['budget']}`.",
        f"Cost is the app's reference token estimate, not a provider invoice. Order: {report['execution_order']} Judge: `course.claims_trajectories.assess` unchanged for both arms.",
        f"Context re-send multiplier: **{report['context_resend_multiplier']}x**; dominant hand-off `{report['dominant_handoff']}` = {report['dominant_handoff_share_percent']:.1f}% of team tokens."])
    return "\n".join(lines)+"\n"


def _verdict(report):
    verdict="keep" if report["team"]["outcome_pass_rate"]>report["single"]["outcome_pass_rate"] and report["team"]["cost_per_claim_usd"]<=2*report["single"]["cost_per_claim_usd"] else "kill"
    lines=[f"Verdict: **{verdict}** for this task and measured cohort.",
        f"Single pass rate: {report['single']['outcome_pass_rate']:.0%}; team: {report['team']['outcome_pass_rate']:.0%}.",
        f"Single p50 latency: {report['single']['p50_latency_ms']:.0f} ms; team: {report['team']['p50_latency_ms']:.0f} ms.",
        f"Single cost/claim: ${report['single']['cost_per_claim_usd']:.6f}; team: ${report['team']['cost_per_claim_usd']:.6f}.",
        f"Context re-send multiplier: {report['context_resend_multiplier']}x; dominant hand-off {report['dominant_handoff']} ({report['dominant_handoff_share_percent']:.1f}% of tokens).",
        "Sunk-cost bias: prior implementation effort is not a reason to keep the team.",
        "Scope limitation: provisional Week-7/8 claims fixtures; required Week-6 claims cohort remains pending."]
    return "\n".join(lines)+"\n"
