import { useEffect, useState } from 'react';
import { ApiClient } from '../../lib/api';
import { useAction } from '../../lib/useAction';
import { RequestState } from '../../components/RequestState';

export function Documents({api}: {api: ApiClient}) {
  const list = useAction<{documents: {source: string; chunks: number}[]}>();
  const mutation = useAction<{chunks?: number; deleted_chunks?: number}>();
  const [files, setFiles] = useState<FileList | null>(null);
  const refresh = () => list.run(signal => api.request('/documents', {signal}));
  useEffect(() => {void refresh();}, [api]);
  return <section className="panel"><h2>Policy documents</h2>
    <p>Upload authorized PDF, DOCX, TXT, Markdown or HTML files. Replacing a filename replaces its indexed version. Use the fictional training corpus for this demo.</p>
    <form onSubmit={async e => {e.preventDefault(); const form = new FormData(); Array.from(files || []).forEach(f => form.append('files', f));
      const result = await mutation.run(signal => api.request('/documents', {method: 'POST', body: form, signal})); if(result) void refresh();}}>
      <label htmlFor="documents">Choose up to ten documents</label><input id="documents" type="file" multiple accept=".pdf,.docx,.txt,.md,.html,.htm" onChange={e => setFiles(e.target.files)} required/>
      <button disabled={mutation.busy || !files?.length || files.length > 10}>Index documents</button>
    </form><RequestState {...mutation}/>{mutation.data && <p role="status">{mutation.data.chunks !== undefined ? `Indexed ${mutation.data.chunks} chunks.` : `Deleted ${mutation.data.deleted_chunks} chunks.`}</p>}
    <RequestState {...list}/><button className="secondary" disabled={list.busy} onClick={() => void refresh()}>Refresh documents</button>
    {list.data?.documents.length === 0 && <p className="empty">No documents indexed. Upload a policy to begin.</p>}
    {!!list.data?.documents.length && <table><thead><tr><th>Source</th><th>Chunks</th><th>Action</th></tr></thead><tbody>{list.data.documents.map(d => <tr key={d.source}><td>{d.source}</td><td>{d.chunks}</td><td><button className="danger" disabled={mutation.busy} aria-label={`Delete ${d.source}`} onClick={async () => {if(window.confirm(`Delete indexed ${d.source}?`)){const result = await mutation.run(signal => api.request(`/documents/${encodeURIComponent(d.source)}`, {method:'DELETE',signal})); if(result) void refresh();}}}>Delete</button></td></tr>)}</tbody></table>}
  </section>;
}
