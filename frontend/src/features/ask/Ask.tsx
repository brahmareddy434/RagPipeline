import { useState } from 'react';
import { ApiClient } from '../../lib/api';
import { useAction } from '../../lib/useAction';
import { RequestState } from '../../components/RequestState';

export type Passage = {id:string; text:string; source:string; page?:number; metadata:Record<string,unknown>; score?:number; rank?:number; semantic_score?:number; keyword_score?:number; fusion_score?:number};
type Answer = {answer:string; abstained:boolean; confidence:string; citations:{chunk_id:string; source:string; quote:string}[]; validation_issues:string[]};
export function Ask({api}: {api:ApiClient}) {
  const [question,setQuestion]=useState('What does exclusion EX-WEAR-01 say?');
  const answer=useAction<Answer>(); const source=useAction<Passage>();
  return <section className="panel"><h2>Ask the policy</h2><p>Answers cite indexed policy passages. Missing evidence should produce an abstention.</p>
    <form onSubmit={e=>{e.preventDefault(); source.cancel(); void answer.run(signal=>api.post('/ask',{question,temperature:0,retrieval:{mode:'hybrid',k:4}},signal));}}>
      <label htmlFor="question">Policy question</label><textarea id="question" value={question} onChange={e=>setQuestion(e.target.value)} required minLength={2} maxLength={2000}/><button disabled={answer.busy}>Ask policy</button>
    </form><RequestState {...answer}/>
    {answer.data && <div className="result"><span className="badge">{answer.data.abstained?'Insufficient evidence':`${answer.data.confidence} confidence`}</span><p>{answer.data.answer}</p>
      {answer.data.validation_issues.length>0 && <details><summary>Validation issues</summary><ul>{answer.data.validation_issues.map((v,i)=><li key={i}>{v}</li>)}</ul></details>}
      {answer.data.citations.map((c,i)=><div key={i}><button className="secondary" onClick={()=>void source.run(signal=>api.request(`/sources/${encodeURIComponent(c.chunk_id)}`,{signal}))}>View source: {c.source}</button><blockquote>{c.quote}</blockquote></div>)}
    </div>}<RequestState {...source}/>{source.data && <article aria-label="Source passage"><h3>{source.data.source}</h3><p>{source.data.text}</p><details><summary>Source provenance</summary><pre>{JSON.stringify({id:source.data.id,page:source.data.page,...source.data.metadata},null,2)}</pre></details></article>}
  </section>;
}
