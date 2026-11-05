import {useEffect} from 'react';
import {ApiClient} from '../../lib/api';
import {useAction} from '../../lib/useAction';
import {RequestState} from '../../components/RequestState';

export function Traces({api}:{api:ApiClient}) {
  const list=useAction<{traces:{trace_id:string;timestamp:string;endpoint:string;status:string}[];notice:string}>();
  const selected=useAction<Record<string,unknown>>();
  const refresh=()=>list.run(signal=>api.request('/traces',{signal}));
  useEffect(()=>{void refresh();},[api]);
  return <section className="panel"><h2>Redacted traces</h2><p>Review the request, evidence, model calls and output. Human observations belong in the separate review worksheet.</p>
    <button disabled={list.busy} onClick={()=>void refresh()}>Refresh traces</button><RequestState {...list}/>
    {list.data && <><p>{list.data.notice}</p>{!list.data.traces.length&&<p className="empty">No recent traces. Ask a policy question first.</p>}<ul>{list.data.traces.map(t=><li key={t.trace_id}><button className="secondary" onClick={()=>void selected.run(signal=>api.request(`/traces/${t.trace_id}`,{signal}))}>{t.endpoint} · {t.status} · {t.timestamp}</button></li>)}</ul></>}
    <RequestState {...selected}/>{selected.data&&<pre aria-label="Trace contents">{JSON.stringify(selected.data,null,2)}</pre>}
  </section>;
}
