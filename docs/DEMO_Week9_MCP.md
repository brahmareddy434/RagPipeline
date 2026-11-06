# Week 9 mentor demo — MCP and insurance claims

## The story

**Week 8:** We measured whether the HR agent took the right steps, added trajectory checks, and reduced unhelpful loops while keeping its answers grounded.

**Week 9:** Keep that bounded agent loop, but connect tools through MCP. The host discovers tools from servers at runtime. Show that a second server can be added through configuration, without changing the agent again.

**Say:** “Ollama runs in our host. MCP servers only provide tools and data; they do not call the model.”

## What I implemented

The local demo connects our fictional policy server and claims server. It discovers **2 policy tools, then 4 tools total** from actual `tools/list` replies. The model calls `claims__get_claim_status` for claim `CLM-2024-88120` and answers “awaiting repair estimate” with supporting evidence. The two-server experiment produced an **empty agent source diff**.

I also added an exclusions resource, a recoverable policy lookup error, raw JSON-RPC capture, and an optional gateway. The gateway lets a status-only token read status while denying adjuster notes; the denial reaches the model, and each call is logged.

These examples use fictional local data; no real claims service or credentials were provided. The model recovered the corrected policy lookup after the error-message change, but both final answers abstained. This demonstrates improved tool recovery, not improved final-answer accuracy.

## Files to show

| File | Purpose |
|---|---|
| `app/agent.py` | Week 8 loop with one-time support for domain prompts and attached MCP context. **Unchanged when adding server two.** |
| `app/mcp_registry.py`, `app/week9.py` | Discover tools and schemas, call MCP servers, attach resource context, and run the existing agent with Ollama. |
| `app/main.py` | Adds `/mcp/tools` and `/mcp/agent/run` API routes. |
| `mcp_servers/policy.py`, `mcp_servers/claims.py` | Our reusable policy server and the fictional claims-system stand-in. |
| `course/insurance/*.json` | Fictional policy and claim records used by those servers. |
| `config/mcp.policy.json`, `config/mcp.claims.json` | The config-only server addition. The second file adds claims to policy. |
| `app/mcp_wire.py`, `course/week9_demo.py` | Capture real local JSON-RPC lines and create the tool-count, diff, transcript, annotation, and risk evidence. |
| `mcp_servers/gateway.py`, `config/mcp.gateway.json`, `config/gateway.scopes.json`, `course/week9_gateway_demo.py` | Optional one-gateway bonus with status/full scopes and a single audit log. |
| `course/week9_peer_client.py`, `tests/test_week9_mcp.py` | Independent SDK client example and integration/regression tests. |
| `run_week9.ps1`, `docs/postman/Week9_MCP_Demo.postman_collection.json` | Demo commands and optional Postman requests. |
| `requirements.txt`, `requirements-lock.txt` | MCP SDK and schema-validator dependencies. |
| `evaluation/week9/submission/` | Saved demo evidence; includes raw wire, source snapshots, diffs, model traces, and five-line risk note. `first_attempt/` retains the original failed recovery experiment. |

## Start the application

From the project folder, install dependencies once if needed:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Start Ollama if it is not already running, then start FastAPI in a terminal and leave it open:

```powershell
.\run_week9.ps1 -Serve
```

Open `http://127.0.0.1:8003/docs`. Use `POST /mcp/agent/run`; `GET /mcp/tools` shows the live discovered tool list. Import `docs/postman/Week9_MCP_Demo.postman_collection.json` if demonstrating with Postman.

## Demo steps for the mentor

1. **Show the Week 8 starting point:** open `app/agent.py`. Its bounded loop makes model decisions; Week 9 supplies a registry and domain prompts to the existing loop.
2. **Show discovery before:** run `.\.venv\Scripts\python.exe -m app.week9 --config config/mcp.policy.json --list`. Point to the two tools returned by `tools/list`.
3. **Show the config diff:** compare `config/mcp.policy.json` with `config/mcp.claims.json`. The new server block adds claims without changing the agent.
4. **Show the measured proof:** open `evaluation/week9/submission/agent_diff.txt`, `config_diff.txt`, and `tool_counts.json`. Counts are **2 → 4**: `policy__search_policy_documents`, `policy__read_policy`; then `claims__get_claim_status`, `claims__get_adjuster_notes`. `finish` is host-side and is not counted.
5. **Show it work:** call `POST /mcp/agent/run` with `{"task":"What is the current status of claim CLM-2024-88120?"}`. Point to the `claims__get_claim_status` entry in `steps` and its citation in the response. The saved live result is `evaluation/week9/submission/claim_query.json`.
6. **Show the wire and recovery:** open `wire.json` to trace `initialize` → `tools/list` → `tools/call`; explain that model calls happen in the host, not in MCP messages or servers. Then show `error_before_after.md`: same malformed policy number; vague error before, corrective docstring/error after. The transcripts are actual Ollama output.
7. **Optional bonus:** open `evaluation/week9/submission/gateway/model_denial.json` and `audit.jsonl`. The status-only token is denied adjuster notes, the denial reaches the model, status still works, and calls record caller, tool, claim number, and outcome.

The risk note is `evaluation/week9/submission/risk_note.md` and has exactly five lines. Review the field explanations in `wire.json` yourself before the mentor meeting so you can explain the messages in your own words.

The independent SDK client proves a second client can use our server; a classmate still needs to connect their own agent for the live peer check. The saved runs used `llama3.2:3b`; 171 tests passed. Postman execution was not verified because its CLI was unavailable under this device's policy.
