# Week 9 mentor guide — give the host more tools through MCP

**Purpose:** Show that the model host can discover claims tools from an MCP server added through configuration.

- **Open the app:** `http://127.0.0.1:5173/#/demo/week9`
- **MCP inventory:** `http://127.0.0.1:5173/#/mcp`

## Before Week 9

The host connected to the policy MCP server and discovered two tools: search policy documents and read a policy. That was enough for policy questions, but not for a question like “What is the status of claim CLM-2024-88120?” The host had no claims-status or adjuster-notes tool to call. Policy wording cannot tell us the current status of one claim.

**Everyday example:** Imagine a receptionist who has a policy handbook but no phone number for the claims desk. The receptionist cannot look up a claim until we connect that department. MCP is the agreed plug that lets the AI host discover and use its tools. This is a realistic fictional claim, not a real customer record.

## What we changed and why

We added a local fictional claims MCP server and connected it in the host configuration. The host now discovers two more tools for claim status and adjuster notes. The model still runs in the host; the MCP server returns data. In the recorded server-one-to-server-two comparison, the agent files were byte-identical. This shows configuration-based tool discovery, not a real insurer integration.

## Main files to show

The key Week 9 additions are the claims server, its config entry, protocol tests and saved evidence. The host/React files show how the wider app uses it.

| File | Status and reason |
|---|---|
| `mcp_servers/claims.py` | **Added:** exposes fictional claim status and adjuster-note tools. |
| `config/mcp.claims.json` | **Added:** registers the claims server next to policy. |
| `mcp_servers/policy.py`, `config/mcp.policy.json` | **Existing:** the before-state policy-only server. |
| `backend/app/infrastructure/mcp/registry.py` | **Host support:** connects and discovers tool schemas. |
| `backend/app/services/mcp_host.py` | **Host support:** lets the model choose discovered tools. |
| `backend/app/controllers/mcp.py` | **Updated:** exposes discovery and bounded demo requests. |
| `frontend/src/features/mcp/Mcp.tsx` | **UI:** displays inventory and MCP traces. |
| `frontend/src/features/runs/MentorDemo.tsx` | **Added:** provides the typed Week 9 before/after flow. |
| `tests/test_week9_mcp.py`, `tests/test_mentor_demo.py` | **Tests:** check local MCP and demo contracts. |
| `evaluation/week9/submission/` | **Evidence:** saved wire, tool-list, config and model-run records. |

## Start the frontend and backend

Use two PowerShell terminals at the repository root. The local MCP servers start as configured by the backend. This demo uses fictional records and needs local Ollama.

**Terminal 1 — backend API**

```powershell
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Check `http://127.0.0.1:8000/docs`. The host process starts and connects to the configured MCP servers.

**Terminal 2 — React frontend**

```powershell
Set-Location frontend
$env:API_PROXY_TARGET = 'http://127.0.0.1:8000'
npm run dev -- --host 127.0.0.1 --port 5173
```

## Show the mentor

1. Open **Week 9 live demo** and read the Before / Issue / Change / After story.
2. Click **Discover before and after tools**. Show two tools before and four after; expand the actual `tools/list` replies.
3. Ask **What is the current status of claim CLM-2024-88120?** and click **Run before and after**.
4. Expand each trace. In the after trace, show `claims__get_claim_status`, its returned observation and the cited answer.
5. Open **MCP tools** to show the configured server inventory and host-run trace.
6. For protocol proof, open `evaluation/week9/submission/wire.json` and point out initialize, tools/list and tools/call messages.

The API routes are `GET /api/v1/mcp/demo/tools?variant=before|after` and `POST /api/v1/mcp/demo/run`. Example body:

```json
{"task":"What is the current status of claim CLM-2024-88120?","variant":"after"}
```

The after response includes a `run` with `answer`, `steps`, and citations, plus `task`, `variant` and `trace_id`. Compare what the live run actually says; model answers can vary.

## Evidence and what it means

`evaluation/week9/submission/tool_counts.json` records **2 → 4** discovered tools. `agent_diff.txt` records no agent-file change for the server-one-to-server-two comparison. `claim_query.json` records a live local-model answer: the claim is awaiting a repair estimate. `wire.json` stores the protocol exchange. `error_before_after.md` and `risk_note.md` preserve separate error and risk evidence. The current backend suite (including local MCP tests) has 218 passing tests; five frontend unit tests and the production build pass. See `docs/architecture/completion-report.md` for the full validation record.

The claims MCP server is fictional and local. Saved wire notes need the learner's own explanation; no independent peer-agent call or real platform credentials/data are claimed. MCP gives a standard way for a host to discover and call tools; it does not guarantee a better answer by itself.

## Simple talk track

“Before Week 9 the host could read policy tools, but it could not look up this claim's status. I added a claims server in configuration. The host discovers two new tools and calls the status tool. The model stays in the host, while the server supplies the claim data. This is a local demo, not a connection to a real insurer.”

**If they ask what MCP does:** “It is a standard way for an AI app to find out which tools another service offers and how to call them. It connects the app to tools; it does not make the answer automatically correct.”
