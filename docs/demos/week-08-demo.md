# Week 8 claims agent demo

**Purpose:** Compare the agent's answer with the steps it used. Measure one prompt change on ten fictional claims.

**Start with:** “I tested ten fictional claims. Five answers passed after one prompt change, but none of the agent runs passed the full path check. I’ll show one example.”

## Start the demo

Open three PowerShell terminals at the repository root (the folder with `course`, `backend` and `frontend`). Use `.venv` and the installed frontend packages.

**Terminal 1 — API**

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Check `http://127.0.0.1:8000/docs`. If `app` cannot be imported, retry with `\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000`.

**Terminal 2 — Frontend**

```powershell
cd frontend
npm run dev
```

**Terminal 3 — Results**

```powershell
Start-Process "http://127.0.0.1:5173/#/benchmarks"
$ev = 'docs/demos/evidence/claims-race'
notepad "$ev/baseline-r4/summary.json"
notepad "$ev/mitigation-r4/comparison.json"
notepad "$ev/mitigation-r4/agent-C04.json"
```

In the app, open **Trajectories** and choose `baseline-r4` or `mitigation-r4`. If port 5173 is busy, use the address Vite prints.

## Walkthrough

1. Open `course/claims_race.py`. Explain: “I set the allowed tool paths first. The answer check scores the reply; the path check scores the tools and inputs.”
2. Open `baseline-r4/summary.json`, then `backend/app/agents/claims.py`. Read the added status-filter instruction. Explain: “Invalid inputs appeared in all ten agent cases, so I changed one instruction and kept the model and budgets the same.”
3. Open `mitigation-r4/comparison.json`. Show: invalid inputs **10 → 2**; answer checks **0 → 5**; repeated-call failures **0 → 8**; full path passes **0 → 0**. The fixed workflow passed 10/10 path checks and 5/10 answer checks. Median latency rose about 27 seconds.
4. In **Trajectories**, select `mitigation-r4`, then C04. Show the passing answer and the repeated `EX-PRE-12` call that failed the path check. Backup: `agent-C04.json`.

Say: “The answer passed, but the agent repeated a policy lookup. Looking only at the final answer would miss that problem.”

## Files to show

| Path | Purpose |
|---|---|
| `course/claims_race.py` | Runs the benchmark and evaluates answers and paths. |
| `backend/app/agents/claims.py` | Claims tools and the changed prompt instruction. |
| `frontend/src/features/runs/Benchmarks.tsx`, `Runs.tsx`, `Traces.tsx` | Benchmark, run, and tool-call views. |
| `docs/demos/evidence/claims-race/baseline-r4/summary.json` | Original agent and fixed-workflow results. |
| `docs/demos/evidence/claims-race/mitigation-r4/comparison.json` | Before/after results and measured tradeoffs. |
| `docs/demos/evidence/claims-race/mitigation-r4/agent-C04.json` | C04 answer, calls, and path assessment. |

## Limits and optional rerun

These are deterministic checks on fictional data, not human labels. The saved r4 evidence has no paired hidden-instruction attack/defense. If asked, say: “I still need to demonstrate that attack and defense.” Do not call this prompt change an injection defense. Cost is an estimate; model: `llama3.2:3b`.

To make a fresh comparison, check `ollama list`, choose a new run label, and wait for the baseline to finish before mitigation:

```powershell
$py = '.\.venv\Scripts\python.exe'; $ev = 'docs/demos/evidence/claims-race'; $run = 'r5'
& $py -m course.claims_race "$ev/baseline-$run"
& $py -m course.claims_race "$ev/mitigation-$run" --baseline "$ev/baseline-$run"
```
