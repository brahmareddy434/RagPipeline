# Week 7 — Task Set C: Race the HR agent against a fixed workflow

**HR policy · 100 marks · Sat on Week 8 Monday**
Short and detailed. Simple English. Read while you work.

---

## 0. What the task asks, and what we built

**The problem in one line:** HR asks the question we should have asked first — does this need to be an agent at all, or would a few hard-coded steps be faster, cheaper and more auditable? Settle it with four numbers, not an opinion.

| # | What the task asks | What we built | Where |
|---|---|---|---|
| 1 | A **third tool**: one job, **enum** parameter, no description overlap | `get_jurisdiction_rules(jurisdiction=IN\|UK\|DE\|US)`. Enum values read from the handbook's own annex headings | `app/agent_tools.py` |
| 2 | The identical task as a **fixed workflow** — same tools, same model, same output contract, **no loop** | 4 hard-coded stages, exactly 1 model call | `app/workflow.py` |
| 3 | Race over the **same 10 questions**, 3+ where a later step depends on an earlier one. Report **4 numbers each** | 10 questions, **7 branching**. pass rate, p50 latency, total tokens, cost/question → `race.csv` | `course/week7_questions.json`, `course/race.py` |
| 4 | **All four budgets** enforced in the loop, plus a log of one clean termination | iterations, tokens, **cost**, wall clock — all checked every lap. Plus 2 extra guards | `AgentBudget`, `week7_budget_termination.json` |
| 5 | A **verdict** applying the decision rule, naming the question class that forces an agent — or saying none does | Section 5, under 150 words | this file |

---

## 1. Run it in this order

```powershell
cd "C:\AI Practice\ollama-rag-fastapi"

# 0. Offline unit tests (no Ollama). Budgets, enum, tool split, race scoring.
.\run_week7.ps1

# 1. See the tool catalogue exactly as the model receives it
.\run_week7.ps1 -Tools

# 2. Force a budget to fire, cleanly, and save the log
.\run_week7.ps1 -BudgetDemo                 # max_steps
.\run_week7.ps1 -BudgetDemo max_cost_usd    # the cost ceiling
.\run_week7.ps1 -BudgetDemo max_tokens
.\run_week7.ps1 -BudgetDemo max_seconds

# 3. The race. Slow on CPU — about 25-40 minutes for 10 questions x 2 systems.
.\run_week7.ps1 -Race

# 4. The demo screen, if you want to show a run live
.\run_week7.ps1 -Serve      # then http://127.0.0.1:8001/agent
```

⚠️ **Do not run the race during the demo.** Show `course/results/race.csv` instead.

---

## 2. The third tool, and the description diff

**Before** — two tools that overlapped, so a jurisdiction question matched both and tool choice was a coin toss:

```
search_policy(query):     "...leave, remote work, expenses, conduct, security, benefits,
                           project addenda..."          <-- claims to cover annexes
lookup_employee(id):      "...project code, work location, probation status..."
                                                        <-- "work location" reads like jurisdiction
```

**After** — one job each, and each says what it does **not** cover:

```
search_handbook(query):              "ONE JOB: the rule that applies to everybody.
                                      ...knows nothing about any individual person and
                                      nothing about country-specific overrides."
get_employee_record(employee_id):    "ONE JOB: facts about that person only...
                                      contains no handbook text and no country rules."
get_jurisdiction_rules(jurisdiction=IN|UK|DE|US):
                                     "ONE JOB: the country override that replaces a
                                      general handbook rule... holds no general rules
                                      and no personal data."
```

Full before/after: `evaluation/week7/tool_descriptions_before.json` and `_after.json`.

**Why this is the fix and a better model is not.** The task's Common Mistakes warns against fixing tool thrash by switching model or bolting "use the correct tool" onto the system prompt. The description bug stays and resurfaces on the next tool. So the boundary is written into the descriptions, and a unit test asserts each of the three says `ONE JOB` and states its exclusion.

**The enum is enforced by Python, not hoped for.** `jurisdiction` is `Literal["IN","UK","DE","US"]`, so `FR` and lowercase `uk` are both rejected before any code runs — and the allowed values are printed into the prompt as `jurisdiction=IN|UK|DE|US`.

---

## 3. The four budgets, and the clean termination

| Budget | Field | What runs away without it |
|---|---|---|
| max iterations | `max_steps` | A model that never chooses `finish` |
| max tokens | `max_tokens` | A scratchpad that keeps growing |
| **max cost** | `max_cost_usd` | The bill, which is the one that actually hurts |
| wall clock | `max_seconds` | A slow tool or a slow model |
| *(extra)* | `max_tool_errors`, `max_repeats` | A tool that cannot succeed; a model re-asking the same thing |

All four are checked **inside the loop on every lap** (`app/agent.py`, the `while True` block). The task warns about declaring constants and never checking three of them — "an unenforced budget is a comment with ambition". A unit test forces the cost ceiling to fire while tokens are still well inside their limit, to prove cost is checked rather than merely recorded.

**Token counting.** The loop re-sends the whole message list every lap, so per-lap tokens must be summed or the agent's cost is understated by multiples. `app/ollama_client.py` records every HTTP call into a context variable and the agent sums **all** of them — `model_calls` in the output is the count, so you can see it is more than one.

**The clean termination log** — `course/results/week7_budget_termination.json`:

```
stop_reason      : max_steps
stop_detail      : Reached the 2 step ceiling.
completed        : false
steps            : 1. get_employee_record(EMP-1007)  ok
                   2. get_jurisdiction_rules(UK)     ok
usage            : 3 model calls, 2833 tokens, $0.000615
answer           : (still produced from the evidence gathered)
```

It stopped, said **which** budget fired, still answered from what it had, and marked `completed: false` so the answer is not trusted silently. It did not spin and it did not crash.

---

## 4. The race numbers

10 questions, 7 of which branch on something only a tool call can reveal (years of service, jurisdiction, project code). Pass conditions were written into `course/week7_questions.json` **before** any run.

<!-- RACE TABLE -->

**Cost is modelled, not billed.** Local Ollama is free, so tokens are priced at a stated reference rate in `app/models.py` ($0.20/M prompt, $0.60/M completion). Only the **ratio** between the two systems means anything.

---

## 5. The verdict

<!-- VERDICT -->

---

## 6. What to show your mentor

**1. The tool catalogue** — `.\run_week7.ps1 -Tools`
Read the last sentence of each description.
> "Each tool says what it cannot do. That is what stops the model reaching for the handbook when it needs a person's record."

**2. The enum rejecting bad input** — `app/agent_tools.py`, `JurisdictionArguments`
> "France is not in the enum, so Python refuses it before any lookup runs. The model cannot invent a country."

**3. The branching question** — on the `/agent` screen, run `q01`: *"EMP-1003 wants to book planned leave next month. How many working days notice must they give?"*
> "The question does not say how long they have worked here. Clause 2.2 says 5 days, clause 2.3 says 10 days for under two years. EMP-1003 has 0.5 years, so the answer is 10 — and you cannot get there without reading the record first."

**4. The budget log** — `course/results/week7_budget_termination.json`
> "Two steps, then the ceiling fired. It named the budget, still answered, and flagged itself as not finished."

**5. `race.csv`** — the eight numbers in one table.

**6. The verdict** — read section 5 out loud, then show the row in the table that supports it.

---

## 7. Mentor cross-check questions and answers

**Q: Is the workflow really doing the same task, or is there a loop hiding in it?**
Same three domain tools, same model, same `GroundedAnswer` output contract, and no `while` or `for` over model calls. Four fixed stages, exactly one generation call. Stage 2 reads the jurisdiction out of stage 1's output, which is data flowing between fixed steps, not the model choosing a path.

**Q: Did you sum tokens across every lap?**
Yes. Every HTTP call is recorded and summed; `model_calls` shows the count so you can check it is more than one. Counting only the final call would understate the agent by multiples, which is the trap in the task's Common Mistakes.

**Q: Are all four budgets actually enforced, or just declared?**
All four are `elif` branches inside the loop, evaluated before every lap. There is a test that makes the cost ceiling fire while tokens are still inside their limit, so cost cannot be the one that is quietly ignored.

**Q: Why p50 latency and not the mean?**
Because one slow run drags a mean and hides the typical experience. I report p50 as the headline and keep mean and p90 in the JSON so the tail is visible too.

**Q: Did you race on questions the agent was always going to win — or lose?**
Neither by design. 7 of 10 branch on a field only a tool can reveal, which is where an agent should earn its cost, and 3 are single-hop or general. The task warns that racing on 10 single-lookup questions hands it to the workflow by construction, so the branching cases are the majority here.

**Q: Your verdict says one thing — does the table agree?**
Yes, and that is the 20-mark criterion. Section 5's verdict quotes the specific rows it rests on. A verdict that contradicted the table would score zero, so it is written from the numbers rather than from what an agent is supposed to do.

**Q: What is the third tool's one job?**
Return the country annex that overrides a general rule. It holds no general rules and no personal data, and its parameter is a closed enum of the four jurisdictions the handbook actually has annexes for.

---

## 8. Submission checklist

| Required | File | Status |
|---|---|---|
| `race.csv` with 8 numbers over the same 10 questions | `course/results/race.csv` | `-Race` |
| The workflow implementation | `app/workflow.py` | done |
| Budget termination log showing which budget fired | `course/results/week7_budget_termination.json` | done |
| Third tool description diff + parameter enums | `evaluation/week7/tool_descriptions_before.json` / `_after.json` | done |
| Verdict naming the question class | section 5 of this file | after `-Race` |
| Agent and workflow each runnable by one command | `.\run_week7.ps1 -Race`, or `--only agent` / `--only workflow` | done |
