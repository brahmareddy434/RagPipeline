# Backend application

Active Python source lives in `app/` here. From the repository root run:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
.\.venv\Scripts\python.exe -m pytest -q
```

The root `app/__init__.py` is only a package-path compatibility shim, not a second implementation. Existing HTTP routes remain available; `/api/v1` aliases support the React client.

| Folder | Responsibility |
|---|---|
| config | Validated environment settings and repository paths |
| controllers | HTTP request/response translation by feature |
| services | Ingestion, answering, evaluation, tools and MCP host use cases |
| agents | Existing agent loop, workflow, tool registry and memory |
| rag | Parsing, chunking, retrieval, prompts and grounded output validation |
| repositories | Persistent vector storage |
| infrastructure | Ollama, traces and MCP transport adapters |
| legacy | HR-specific rules preserved for regression compatibility |
| static/legacy | Existing HTML screens, retained until React parity |

`bootstrap.py` constructs dependencies; `main.py` manages lifecycle and router registration. Historical snapshots under `evaluation/week9` retain their original bytes. Migration verification: all **171 tests passed** (35.04s, three dependency warnings).
