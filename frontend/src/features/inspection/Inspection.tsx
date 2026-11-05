import {useState} from 'react';
import {ApiClient} from '../../lib/api';
import {useAction} from '../../lib/useAction';
import {RequestState} from '../../components/RequestState';
import type {Passage} from '../ask/Ask';

export function Inspection({api}:{api:ApiClient}) {
  const [question,setQuestion]=useState('What does EX-FLOOD-02 exclude?');
  const [mode,setMode]=useState('hybrid');
  const action=useAction<{retrieved:Passage[];note:string}>();
  return <section className="panel"><h2>Retrieval inspection</h2><p>Inspect exact chunk IDs, ranks and versions before changing retrieval.</p>
    <form onSubmit={e=>{e.preventDefault();void action.run(signal=>api.post('/inspect',{question,retrieval:{mode,k:3}},signal));}}>
      <label htmlFor="inspect-question">Retrieval question</label><input id="inspect-question" value={question} onChange={e=>setQuestion(e.target.value)} required minLength={2} maxLength={2000}/>
      <label htmlFor="retrieval-mode">Strategy</label><select id="retrieval-mode" value={mode} onChange={e=>setMode(e.target.value)}><option value="semantic">Semantic</option><option value="hybrid">BM25 + RRF (60)</option><option value="keyword">Keyword</option></select><button disabled={action.busy}>Inspect retrieval</button>
    </form><RequestState {...action}/>{action.data && <><p>{action.data.note}</p>{!action.data.retrieved.length&&<p className="empty">No matching passages.</p>}{action.data.retrieved.map(r=><article key={r.id} className="result"><h3>Rank {r.rank}: {r.source}</h3><p>{r.text}</p><details><summary>IDs, scores and provenance</summary><pre>{JSON.stringify({...r,text:undefined},null,2)}</pre></details></article>)}</>}
  </section>;
}
