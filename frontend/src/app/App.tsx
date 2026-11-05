import { useEffect, useMemo, useState } from 'react';
import { HashRouter, NavLink, Route, Routes } from 'react-router-dom';
import { ApiClient } from '../lib/api';
import { Tools } from '../features/tools/Tools';
import { Documents } from '../features/documents/Documents';
import { Ask } from '../features/ask/Ask';
import { Inspection } from '../features/inspection/Inspection';

type Identity = {tenant: string; role: string};
export function App() {
  const [token, setToken] = useState('');
  const [draft, setDraft] = useState('');
  const [identity, setIdentity] = useState<Identity>();
  const [error, setError] = useState('');
  const api = useMemo(() => new ApiClient(token), [token]);
  useEffect(() => {
    const controller = new AbortController(); setIdentity(undefined); setError('');
    api.request<Identity>('/session', {signal: controller.signal}).then(setIdentity).catch(e => {if (!controller.signal.aborted) setError(e.message);});
    return () => controller.abort();
  }, [api]);
  return <HashRouter><div className="layout">
    <aside><a className="brand" href="#/">Claims<br/><strong>Workbench</strong></a><p className="eyebrow">AI ENGINEERING · WEEKS 01–09</p>
      <nav aria-label="Main navigation"><NavLink to="/">Overview</NavLink><NavLink to="/tools">Structured tools</NavLink><NavLink to="/documents">Documents</NavLink><NavLink to="/ask">Policy Q&amp;A</NavLink><NavLink to="/inspect">Retrieval inspection</NavLink></nav>
      <div className="sidebar-note">Fictional training data<br/>Human review required</div>
    </aside>
    <main><header><div><p className="eyebrow">INSURANCE CLAIMS</p><h1>Evidence before answers.</h1></div><span className="badge">{identity ? `${identity.tenant} · ${identity.role}` : 'Connecting'}</span></header>
      {!identity ? <section className="panel"><h2>Connect to your workspace</h2><p>Local mode connects automatically. For a protected server, enter your scoped access token.</p>
        {error ? <p role="alert" className="error">{error}</p> : <p role="status">Checking access…</p>}
        <form onSubmit={e => {e.preventDefault(); setToken(draft); setDraft('');}}><label htmlFor="token">Access token</label><input id="token" type="password" autoComplete="off" value={draft} onChange={e => setDraft(e.target.value)} required/><button>Connect</button></form><p>Tokens stay in memory and are cleared on reload.</p></section>
        : <div key={identity.tenant + token}><Routes>
          <Route path="/" element={<section className="panel"><h2>A traceable claims assistant</h2><p>Explore structured tools, policy evidence, agent trajectories and MCP discovery as each weekly capability is integrated.</p><div className="cards"><article><span className="eyebrow">FOUNDATIONS</span><h3>Predict, validate, act</h3><p>Models propose outputs. Application code validates and executes them.</p></article><article><span className="eyebrow">REVIEW</span><h3>Show the evidence</h3><p>Learning materials distinguish measured results from human acceptance still needed.</p></article></div><a href="/course/guides/01_language_models.md">Read Week 01 foundations</a></section>}/>
          <Route path="/tools" element={<Tools api={api}/>}/>
          <Route path="/documents" element={<Documents api={api}/>}/>
          <Route path="/ask" element={<Ask api={api}/>}/>
          <Route path="/inspect" element={<Inspection api={api}/>}/>
          <Route path="*" element={<section className="panel"><h2>Page not found</h2><a href="#/">Return to overview</a></section>}/>
        </Routes></div>}
      <footer>Claims Workbench · Read-only training decisions, never payment authorization.</footer>
    </main></div></HashRouter>;
}
