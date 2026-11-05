"""Live ten-case comparison and a separate one-prompt-change mitigation run."""
import argparse
import asyncio
import hashlib
import json
from datetime import datetime,timezone
from pathlib import Path
from app.agents.claims import ClaimsTools,ClaimsWorkflow,claims_agent,task_for,MITIGATION_PROMPTS
from app.repositories.claims import FictionalClaims
from app.config.paths import PROJECT_ROOT
from app.config.settings import get_settings
from app.schemas import AgentBudget
from app.infrastructure.ollama import OllamaClient
from app.infrastructure.redaction import redact
from course.claims_review import write
from course.claims_trajectories import expectations,assess,summarize

SOURCES=['backend/app/agents/claims.py','backend/app/agents/loop.py','backend/app/infrastructure/ollama.py',
         'backend/app/infrastructure/budgets.py','backend/app/repositories/claims.py','course/claims_trajectories.py',
         'course/insurance/triage-claims.json','course/insurance/claims-policy-2026.txt']

async def run(output,baseline=None):
    if output.exists() and any(output.iterdir()):
        raise ValueError("Output directory already contains an attempt. Choose a new directory; keep partial evidence unchanged.")
    output.mkdir(parents=True,exist_ok=True)
    cfg=get_settings();registry=ClaimsTools(FictionalClaims());cases=expectations(registry.repository)
    budget=AgentBudget(max_steps=6,max_tokens=32000,max_seconds=180,max_cost_usd=.03)
    manifest={'timestamp':datetime.now(timezone.utc).isoformat(),'model':cfg.ollama_chat_model,'budget':budget.model_dump(),
              'provenance':'Actual local model runs over ten assistant-authored fictional claims; outcome tests are deterministic proxies, not human acceptance.',
              'cost':'Modelled reference USD at prompt 0.20 / completion 0.60 per million tokens; not an Ollama invoice.',
              'source_sha256':{p:hashlib.sha256((PROJECT_ROOT/p).read_bytes()).hexdigest() for p in SOURCES},
              'mitigation':bool(baseline)}
    if baseline:
        old=json.loads((baseline/'manifest.json').read_text())
        if any(old[k]!=manifest[k] for k in ('model','budget','source_sha256')):raise ValueError('Frozen model/budget/source changed; mitigation comparison rejected.')
        prior=json.loads((baseline/'summary.json').read_text())
        modes={k:v for k,v in prior['agent']['modes'].items() if k!='pass'}
        if not modes:raise ValueError('No measured failure mode justifies a mitigation.')
        top_mode=max(modes,key=modes.get)
        if top_mode not in MITIGATION_PROMPTS:raise ValueError(f'No predeclared single prompt mitigation for measured top mode: {top_mode}.')
        manifest['mitigation_mode']=top_mode
    write(output/'manifest.json',manifest);write(output/'expected-paths.json',cases)
    provider=OllamaClient(cfg.ollama_base_url,cfg.ollama_chat_model,cfg.ollama_embed_model,cfg.ollama_timeout_seconds)
    rows={'agent':[],'workflow':[]}
    try:
        for i,case in enumerate(cases,1):
            for approach in (['agent'] if baseline else ['agent','workflow']):
                runner=claims_agent(provider,registry,mitigation=manifest.get('mitigation_mode',False))
                result=await runner.run(task_for(case['claim_id']),budget=budget) if approach=='agent' else await ClaimsWorkflow(provider,registry).run(case['claim_id'],budget)
                row={'case_id':f'C{i:02}','assessment':assess(result,case,registry),'run':result.model_dump(mode='json')}
                # Stable identifiers belong to the explicitly fictional public fixture and
                # must remain available to reproduce and assess tool paths.
                rows[approach].append(row);write(output/f'{approach}-C{i:02}.json',row)
                print(f"{approach} C{i:02}: {row['assessment']['mode']} / {result.stop_reason} / {result.usage['total_tokens']} tokens",flush=True)
        summary={name:summarize(records) for name,records in rows.items() if records}
        write(output/'summary.json',summary)
        # Actual clean admission-limit termination with zero hidden finalization.
        limited=await claims_agent(provider,registry).run(task_for(cases[0]['claim_id']),budget=AgentBudget(max_tokens=500))
        write(output/'budget-stop.json',limited.model_dump(mode='json'))
        if baseline:
            before=json.loads((baseline/'summary.json').read_text())['agent'];after=summary['agent']
            write(output/'comparison.json',{'only_change':f"one additional prompt instruction for the measured top mode {manifest['mitigation_mode']}",
                 'before':before,'after':after,'mode_deltas':{m:after['modes'].get(m,0)-before['modes'].get(m,0) for m in sorted(set(before['modes'])|set(after['modes']))},
                 'price':{k:after[k]-before[k] for k in ('p50_latency_ms','total_tokens','mean_cost_per_claim_usd','outcome_pass_rate')}})
        print(json.dumps(summary,indent=2),flush=True)
    finally:await provider.close()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--baseline',type=Path)
    a=p.parse_args();asyncio.run(run(a.output,a.baseline))
