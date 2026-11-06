# Week 9 MCP demo

**Purpose:** Show the app discovering tools from MCP servers. Add claims tools through configuration without changing the agent.

**Start with:** “The host runs the model and discovers tools from servers. I’ll show two policy tools, then add two claims tools through configuration.”

## Start the demo

Open three PowerShell terminals at the repository root. Use `.venv`, installed frontend packages, and local Ollama with `llama3.2:3b`.

**Terminal 1 — API**

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Check `http://127.0.0.1:8000/docs`.

**Terminal 2 — Frontend**

```powershell
cd frontend
npm run dev
```

**Terminal 3 — App and saved results**

```powershell
Start-Process "http://127.0.0.1:5173/#/mcp"
notepad evaluation/week9/submission/tool_counts.json
notepad evaluation/week9/submission/agent_diff.txt
notepad evaluation/week9/submission/claim_query.json
```

In the app, choose **MCP tools**. If port 5173 is busy, use Vite's printed address.

## Walkthrough

### Typed-query demonstration

Open `http://127.0.0.1:5173/#/demo/week9` (**Week 9 live demo**). Restart the API after updating backend code. Read the four on-screen stages: policy-only tools, missing claim-record access, adding claims server configuration, discovered claim lookups.

1. Click **Discover before and after tools**. Show actual `tools/list` responses: two policy tools before, four tools after. Host-local `finish` is excluded.
2. Ask **What is the current status of claim CLM-2024-88120?** and click **Run before and after**. The same prompt and host code run against the two configurations. Explain why the before arm lacks claim-status evidence; inspect what it actually says rather than assuming success or abstention.
3. Expand **Tool trajectory** in the after result. Show the discovered `claims__get_claim_status` call, its server observation and the grounded answer. Explain that the model runs in the host. Each arm has a 180-second model-run budget; MCP setup occurs first.
4. Week 9 uses the older `CLM-2024` MCP fixture; Week 8 uses the separate `CLM-2026` triage fixture. Use the page's example so identifiers match its tools.

New contracts: `GET /api/v1/mcp/demo/tools?variant=before|after`, and `POST /api/v1/mcp/demo/run` with `{ "task": "What is the current status of claim CLM-2024-88120?", "variant": "after" }`. Responses contain real discovery or `run`, `variant`, `task`, and `trace_id`. The config selector in `services/mcp_host.py` accepts only the two fixed files. The model, fixtures, database and original submission snapshots are unchanged. `MentorDemo.tsx` displays fresh runs; the existing MCP page remains usable.

### Original protocol evidence walkthrough

1. Open `config/mcp.policy.json` and `config/mcp.claims.json`, then `evaluation/week9/submission/config_diff.txt`. Explain: “The second config adds the claims server.”
2. Click **Discover tools** or open `tool_counts.json`. Show two tools before and four after: `policy__search_policy_documents`, `policy__read_policy`, `claims__get_claim_status`, `claims__get_adjuster_notes`. The host-only `finish` action is not counted.
3. Open `agent_diff.txt`. Explain: “In this server-one-to-server-two comparison, the agent source did not change.”
4. In the question box, run: “What is the current status of claim CLM-2024-88120?” Show `claims__get_claim_status` in the trace and open `claim_query.json`. The saved answer says “awaiting repair estimate.”
5. Open `wire.json`. Explain simply: “The host asks for tools, then calls one. The model runs in the host, not in the MCP server.”
6. Open `error_before_after.md`. The same invalid policy lookup gets a clearer error after the change. The saved model runs recovered a tool call, but both final answers abstained.

## Files to show

| Path | Purpose |
|---|---|
| `config/mcp.policy.json`, `config/mcp.claims.json` | Policy setup and claims-server configuration. |
| `mcp_servers/policy.py`, `mcp_servers/claims.py` | Local MCP servers with fictional data. |
| `backend/app/services/mcp_host.py`, `frontend/src/features/mcp/Mcp.tsx` | Host tool calls and React discovery page. |
| `evaluation/week9/submission/tool_counts.json`, `agent_diff.txt` | Before/after tools and agent source comparison. |
| `evaluation/week9/submission/wire.json`, `claim_query.json` | Captured MCP messages and saved model run. |
| `evaluation/week9/submission/error_before_after.md`, `risk_note.md` | Error recovery and five-line risk note. |

## Limits and optional rerun

The data is fictional; no real claims platform is connected. A personal explanation of the wire notes and a separate person's agent call are still needed. The gateway demo is local and does not prove production security.

To run again with Ollama, check `ollama list`. This writes timestamped files under `course/results/week9/`:

```powershell
.\.venv\Scripts\python.exe -m course.week9_demo --live --output course/results/week9
```

Validation already recorded: 199 backend tests, 5 frontend tests, production build, 5/5 browser journeys, and 6/6 local Postman requests passed. Postman cloud publishing was not run.
