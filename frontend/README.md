# React application

Run `npm ci`, `npm run dev` from this directory. Start the backend from the repository root with `.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000`. Open http://127.0.0.1:5173.

React/TypeScript/Vite uses hash routing, one typed client and cancellable requests. `/api` proxies to port 8000; override with `API_PROXY_TARGET`. Local mode checks loopback and browser origin. Protected mode accepts a scoped Bearer token, held only in memory.

`npm run build` type-checks and builds `dist`, served by the backend on restart. `npm test` runs component/client tests. Legacy `/agent` remains available. All nine weeks are authorized; see `docs/demos` for actual acceptance and evidence limitations.
