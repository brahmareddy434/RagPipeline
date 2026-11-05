import {useEffect,useState} from 'react';
import {ApiClient} from '../../lib/api';
import {useAction} from '../../lib/useAction';
import {RequestState} from '../../components/RequestState';
export type Run={answer:string;abstained:boolean;stop_reason:string;stop_detail:string;usage:Record<string,unknown>;steps:Record<string,unknown>[];citations:{chunk_id:string;source:string;quote:string}[];evidence:{id:string;text:string;source:string}[]};
export function RunView({run,title}:{run:Run;title:string}) {
  return <article className="panel"><h3>{title}</h3><span className="badge">{run.stop_reason}</span><p>{run.answer}</p><p>{run.stop_detail}</p>
    <details><summary>Usage and budgets</summary><pre>{JSON.stringify({...run.usage,provider_calls:undefined},null,2)}</pre></details>
    <details><summary>Tool trajectory ({run.steps.length} steps)</summary><pre>{JSON.stringify(run.steps,null,2)}</pre></details>
    {run.citations.map((c,i)=><details key={i}><summary>Evidence: {c.source}</summary><blockquote>{c.quote}</blockquote><p>{run.evidence.find(e=>e.id===c.chunk_id)?.text||'Evidence unavailable in this run.'}</p></details>)}
  </article>;
}
export function Runs({api}:{api:ApiClient}) {
  const [claim,setClaim]=useState('CLM-2026-10002');
  const fixtures=useAction<{claims:{claim_id:string;status:string}[];provenance:string}>();
  const action=useAction<{agent:Run;workflow:Run}>();
  useEffect(()=>{void fixtures.run(signal=>api.request('/claims/fixtures',{signal}));},[api]);
  return <><section className="panel"><h2>Agent and fixed workflow</h2><p>Compare the same fictional claim sequentially using the same model, tools and grounded output contract.</p><RequestState {...fixtures}/>
    <form onSubmit={e=>{e.preventDefault();void action.run(signal=>api.post('/claims/run',{claim_id:claim,approach:'race'},signal));}}><label htmlFor="claim">Claim</label><select id="claim" value={claim} onChange={e=>setClaim(e.target.value)}>{fixtures.data?.claims.map(c=><option key={c.claim_id} value={c.claim_id}>{c.claim_id} - {c.status}</option>)}</select><button disabled={action.busy||!fixtures.data}>Compare approaches</button></form><RequestState {...action}/></section>
    {action.data&&<div className="cards"><RunView title="Agent" run={action.data.agent}/><RunView title="Fixed workflow" run={action.data.workflow}/></div>}</>;
}
