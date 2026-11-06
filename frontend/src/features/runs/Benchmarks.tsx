import {useEffect} from 'react';
import {ApiClient} from '../../lib/api';
import {useAction} from '../../lib/useAction';
import {RequestState} from '../../components/RequestState';
import {RunView,type Run} from './Runs';
type Metrics={outcome_pass_rate:number;trajectory_pass_rate:number;outcome_minus_trajectory_gap:number;p50_latency_ms:number;total_tokens:number;mean_cost_per_claim_usd:number;cost_p50_usd:number;cost_max_usd:number;modes:Record<string,number>};
export function Benchmarks({api}:{api:ApiClient}) {
  const reports=useAction<{reports:Record<string,Record<string,Metrics>>;comparison:unknown;notice:string}>();
  const selected=useAction<{run:Run;assessment:Record<string,unknown>;case_id:string}>();
  const refresh=()=>reports.run(signal=>api.request('/claims/benchmarks',{signal}));
  useEffect(()=>{void refresh();},[api]);
  return <section className="panel"><h2>Trajectory benchmarks</h2><button onClick={()=>void refresh()} disabled={reports.busy}>Refresh benchmarks</button><RequestState {...reports}/>
    {reports.data&&<><p>{reports.data.notice}</p>{!Object.keys(reports.data.reports).length&&<p className="empty">The live benchmark has not completed yet.</p>}
      {Object.entries(reports.data.reports).map(([phase,approaches])=><article key={phase}><h3>{phase}</h3><div className="table-scroll"><table><thead><tr><th>Approach</th><th>Outcome</th><th>Path</th><th>Gap</th><th>Latency p50</th><th>Tokens</th><th>Cost/claim</th></tr></thead><tbody>{Object.entries(approaches).map(([name,m])=><tr key={name}><td>{name}</td><td>{m.outcome_pass_rate*100}%</td><td>{m.trajectory_pass_rate*100}%</td><td>{m.outcome_minus_trajectory_gap*100} points</td><td>{m.p50_latency_ms.toFixed(0)} ms</td><td>{m.total_tokens}</td><td>${m.mean_cost_per_claim_usd.toFixed(6)}</td></tr>)}</tbody></table></div>
        <details><summary>All trajectory metrics and modes</summary><pre>{JSON.stringify(approaches,null,2)}</pre></details><div className="row">{Array.from({length:10},(_,i)=>`C${String(i+1).padStart(2,'0')}`).map(id=><button className="secondary" key={id} onClick={()=>void selected.run(signal=>api.request(`/claims/benchmarks/${phase}/agent/${id}`,{signal}))}>{id}</button>)}</div></article>)}
      {!!reports.data.comparison&&<details><summary>Single mitigation: regressions and measured price</summary><pre>{JSON.stringify(reports.data.comparison,null,2)}</pre></details>}</>}
    <RequestState {...selected}/>{selected.data&&<><pre>{JSON.stringify(selected.data.assessment,null,2)}</pre><RunView run={selected.data.run} title={selected.data.case_id}/></>}
  </section>;
}
