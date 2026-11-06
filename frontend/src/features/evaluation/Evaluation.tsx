import {useEffect} from 'react';
import {ApiClient} from '../../lib/api';
import {useAction} from '../../lib/useAction';
import {RequestState} from '../../components/RequestState';
type Report={provenance:string;notice:string;deterministic_criteria:number;judge_criteria:number;modes:Record<string,{passed:number;total:number}>;cases:{id:string;mode:string;passed:boolean;judge:string;assertions:Record<string,boolean>}[]};
export function Evaluation({api}:{api:ApiClient}) {
  const action=useAction<Report>();
  useEffect(()=>{void action.run(signal=>api.request('/claims/evaluation',{signal}));},[api]);
  return <section className="panel"><h2>Claims evaluation</h2><RequestState {...action}/>{action.data&&<><p>{action.data.provenance}</p><p>{action.data.notice}</p><p>{action.data.deterministic_criteria} deterministic criteria · {action.data.judge_criteria} binary judge criterion, pending blind labels.</p>
    <table><thead><tr><th>Mode</th><th>Assertion passes</th><th>Rate</th></tr></thead><tbody>{Object.entries(action.data.modes).map(([mode,m])=><tr key={mode}><td>{mode}</td><td>{m.passed}/{m.total}</td><td>{Math.round(m.passed/m.total*100)}%</td></tr>)}</tbody></table>
    <details><summary>Case-level checks</summary><pre>{JSON.stringify(action.data.cases,null,2)}</pre></details></>}</section>;
}
