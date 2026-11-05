import {useEffect,useState} from 'react';
import {ApiClient} from '../../lib/api';
import {useAction} from '../../lib/useAction';
import {RequestState} from '../../components/RequestState';
import {RunView,type Run} from '../runs/Runs';

export function Mcp({api}:{api:ApiClient}) {
  const inventory=useAction<{count:number;names:string[];tools_list_responses:unknown[]}>();
  const action=useAction<{discovery:unknown[];run:Run;trace_id:string}>();
  const [task,setTask]=useState('What is the current status of claim CLM-2024-88120?');
  const discover=()=>inventory.run(signal=>api.request('/mcp/tools',{signal}));
  useEffect(()=>{void discover();},[api]);
  return <><section className="panel"><h2>MCP discovery</h2><p>Tools come from the operator-configured local fictional servers. The model stays in the host.</p>
    <button disabled={inventory.busy} onClick={()=>void discover()}>Discover tools</button><RequestState {...inventory}/>
    {inventory.data&&<><p>{inventory.data.count} server tools discovered (host finish excluded).</p><ul>{inventory.data.names.map(n=><li key={n}>{n}</li>)}</ul><details><summary>Actual tools/list responses</summary><pre>{JSON.stringify(inventory.data.tools_list_responses,null,2)}</pre></details></>}
    <form onSubmit={e=>{e.preventDefault();void action.run(signal=>api.post('/mcp/agent/run',{task,budget:{max_steps:4,max_seconds:180,max_tokens:32000}},signal));}}><label htmlFor="mcp-task">Claims question</label><textarea id="mcp-task" value={task} onChange={e=>setTask(e.target.value)} required minLength={2} maxLength={2000}/><button disabled={action.busy}>Run discovered tools</button></form><RequestState {...action}/></section>
    {action.data&&<RunView title="MCP host run" run={action.data.run}/>}</>;
}
