import {useEffect,useState} from 'react';
import {ApiClient} from '../../lib/api';
import {useAction} from '../../lib/useAction';
import {RequestState} from '../../components/RequestState';
import {RunView,type Run} from './Runs';

const example='Summarize status and unresolved issues for CLM-2026-10001, including any exclusion review needed. Cite the relevant policy clauses. Do not decide coverage.';
type Pair={claim_id:string;provenance:string;arm:string;single?:Run;team?:Run;task_state?:string};
type Race={generated_at_utc:string;manifest:{case_ids:string[];cohort_provenance:string;exact_week6_cohort:boolean};single:Record<string,number>;team:Record<string,number>;context_resend_multiplier:number;dominant_handoff:string;dominant_handoff_share_percent:number;artifacts:Record<string,string>};
type Card=Record<string,unknown>;
const fmt=(value:unknown,digits=2)=>typeof value==='number'?value.toFixed(digits):'Unavailable';

export function Week10Demo({api}:{api:ApiClient}) {
  const [claim,setClaim]=useState('CLM-2026-10001');const [task,setTask]=useState(example);
  const query=useAction<Pair>();const race=useAction<Race>();const card=useAction<Card>();const failure=useAction<Pair>();
  useEffect(()=>{void card.run(signal=>api.request('/claims/team/agent-card',{signal}));void race.run(signal=>api.request('/claims/team/race/latest',{signal}));},[api]);
  const send=(arm:'both'|'failure')=>query.run(signal=>api.post('/claims/team/run',{claim_id:claim,arm,task},signal));
  return <>
    <section className="panel"><h2>Week 10: race one claims agent against a small team</h2>
      <p>Earlier weeks used one claims agent to read a record, notes and cited policy clauses. Week 10 adds a manager, a coverage/exclusions specialist and an adjuster-notes specialist. A paired live query gives both arms the same question, claim fixture, model and budget; the ten-case race applies the unchanged Week 8 deterministic judge to both arms.</p>
      <ol className="demo-story"><li><h3>Before</h3><p>The single agent chose and executed the claims tools itself. Its ten-case trajectory evidence is recorded in the Week 8 benchmark.</p></li><li><h3>Issue tested</h3><p>Could separate specialist instructions improve claim summaries enough to justify duplicated prompts, extra latency and token cost?</p></li><li><h3>What changed</h3><p>A manager plans two narrow tasks, the specialists run concurrently on scoped evidence, and the manager synthesizes a grounded administrative summary. This is a local orchestration pattern, not a deployed A2A service.</p></li><li><h3>After</h3><p>Run the same live question through both arms, inject a coverage-worker 500, or run the paired ten-case race. Use the measured outputs below to decide whether to keep the team.</p></li></ol>
      <p role="note"><strong>Dataset limitation:</strong> the repository has no identified ten-case Week-6 Task D claims set and judge. The paired race is transparently provisional on the existing ten Week-7/8 claims; it does not satisfy W10-AC01.</p>
      <label htmlFor="w10-claim">Fictional claim</label><select id="w10-claim" value={claim} disabled={query.busy||failure.busy} onChange={e=>{const next=e.target.value;setTask(value=>value.replace(claim,next));setClaim(next);}}>{Array.from({length:10},(_,i)=>`CLM-2026-${String(10001+i).padStart(5,'0')}`).map(id=><option key={id}>{id}</option>)}</select>
      <label htmlFor="w10-query">Question sent to both arms</label><textarea id="w10-query" rows={3} value={task} disabled={query.busy} onChange={e=>setTask(e.target.value)} minLength={2} maxLength={2000}/>
      <div className="row"><button disabled={query.busy||failure.busy||task.trim().length<2||!task.includes(claim)} onClick={()=>void send('both')}>Run single and team</button><button className="secondary" disabled={query.busy||failure.busy} onClick={()=>setTask(example.replace('CLM-2026-10001',claim))}>Use example</button><button className="secondary" disabled={query.busy||failure.busy||!task.includes(claim)} onClick={()=>void failure.run(signal=>api.post('/claims/team/run',{claim_id:claim,arm:'failure',task},signal))}>Inject coverage worker 500</button></div>
      {query.busy&&<p role="status">Running both arms sequentially; each has a bounded local-model budget. This may take several minutes.</p>}{failure.busy&&<p role="status">Running the manager and injecting one coverage worker failure.</p>}
      <RequestState {...query}/><RequestState {...failure}/>
    </section>
    {query.data&&<><p>Same fictional claim: {query.data.claim_id}. Provenance: {query.data.provenance}.</p><div className="cards">{query.data.single&&<RunView title="Before: single agent" run={query.data.single}/ >}{query.data.team&&<RunView title="After: manager + two specialists" run={query.data.team}/>}</div></>}
    {failure.data?.team&&<section className="panel"><h3>Injected failure result</h3><p>A simulated in-process HTTP 500 is injected at the required coverage/exclusions hand-off. It is not a remote HTTP call. The local orchestration should report the worker failure and leave coverage undetermined.</p><RunView title="Failure case" run={failure.data.team}/></section>}
    <section className="panel"><h3>Paired ten-case race</h3><p>Saved race results load automatically. Running a new race calls the local model for all ten single-agent cases, all ten team cases, and one separate injected-failure case; each run is saved to a fresh evidence directory.</p><button disabled={race.busy||query.busy||failure.busy} onClick={()=>void race.run(signal=>api.post('/claims/team/race',{},signal))}>Run a new ten-case race</button><RequestState {...race}/>
      {race.data&&<><p>Generated: {race.data.generated_at_utc} · multiplier: {race.data.context_resend_multiplier}× · largest hand-off: {race.data.dominant_handoff} ({race.data.dominant_handoff_share_percent}%).</p><pre>{race.data.artifacts['race_table.md']}</pre><details><summary>Per-hand-off token log</summary><pre>{race.data.artifacts['handoffs.log']}</pre></details><details><summary>Injected failure</summary><pre>{race.data.artifacts['failure_case.md']}</pre></details><details><summary>Verdict</summary><pre>{race.data.artifacts['verdict.md']}</pre></details><p>Evidence directory: {race.data.artifacts.run_id}</p></>}
    </section>
    <section className="panel"><h3>Proposed AgentCard</h3><p>This describes the local agent's skills, JSON modes and auth. There is no A2A protocol endpoint in this application.</p><RequestState {...card}/>{card.data&&<pre>{JSON.stringify(card.data,null,2)}</pre>}<p>A worker 500 is a terminal failed task for this run; input-required is appropriate only if a human adjuster must provide missing information. A2A adds interoperable agent discovery and task states over the worker capability description; a plain REST call can invoke a worker, but does not itself standardize that agent lifecycle.</p></section>
  </>;
}
