import { useState } from 'react';
import { ApiClient } from '../../lib/api';
import { useAction } from '../../lib/useAction';
import { RequestState } from '../../components/RequestState';

export function Tools({api}: {api: ApiClient}) {
  const [question, setQuestion] = useState('Calculate 2500 - 500');
  const action = useAction<{tool: string; result: string | number; executed_by: string}>();
  return <section className="panel"><h2>Structured tools</h2>
    <p>The model selects an action. Validated Python code performs the calculation or demonstration lookup.</p>
    <form onSubmit={e => { e.preventDefault(); void action.run(signal => api.post('/tools/run', {question}, signal)); }}>
      <label htmlFor="tool-question">Question</label><input id="tool-question" value={question} onChange={e => setQuestion(e.target.value)} required minLength={2} maxLength={2000}/>
      <button disabled={action.busy}>Run tool</button>
    </form>
    <RequestState {...action}/>
    {action.data && <div className="result" aria-live="polite"><span className="badge">{action.data.tool}</span><h3>{String(action.data.result)}</h3><p>Executed by {action.data.executed_by}</p></div>}
  </section>;
}
