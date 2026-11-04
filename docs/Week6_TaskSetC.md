# Week 6 — Task Set C: Validate the policy-answer judge before you trust its number

**HR policy · 100 marks · Sat on Week 7 Monday**
Short and detailed. Simple English. Read while you work.

---

## 0. What the task asks, and what we built

**The problem in one line:** our eval prints a correctness score that comes from an LLM judge nobody has ever checked against a human. HR is about to trust it. Prove the judge agrees with you — or find out it does not.

| # | What the task asks | What we built | Where |
|---|---|---|---|
| 1 | 25+ cases, each tagged with one Week-5 taxonomy mode, 2+ verbatim regressions, one command printing pass rate **by mode** | **33 cases**, all 7 taxonomy modes, **3 verbatim regressions** from real failed traces | `evaluation/week6/eval_set.json`, `run_evals.py` |
| 2 | Move 2+ criteria out of the judge into assertions, delete them from the judge prompt, report assertion vs judged counts | **4 criteria moved**, judge left with **1** criterion. Counts printed, not claimed | `app/week6_assertions.py`, `judge_v1.txt` |
| 3 | 25 hand labels, blind, saved **before** the judge runs, with proof of ordering | Blind labelling tool + SHA256 sealed receipt. The judge **refuses to run** without it | `label_blind.py`, `labels_receipt.json` |
| 4 | Run judge, measure agreement, iterate using 2 of its **own** disagreements, re-measure | `agreement.py` does all four steps and writes `judge_v2.txt` itself | `agreement.py` |
| 5 | Prediction written **before** iterating, then scored honestly | Written and dated | `evaluation/week6/prediction.txt` |

**⚠️ One part is yours and cannot be automated.** Requirement 3 is worth **25 marks and scores zero without ordering evidence**. I built the tool that enforces the protocol, but *you* must do the labelling. A label I wrote for you would not be your blind judgement — and "pre-filled labels you review" is the exact failure mode in the task's Common Mistakes list.

---

## 1. Run it in this order (the tools enforce the order)

```powershell
cd "C:\AI Practice\ollama-rag-fastapi"

# 0. Offline unit tests (no Ollama). Proves the machinery, not the model.
.\run_evals.ps1 -Tests

# 1. Generate the answers once. Live cases answered now; regressions replayed verbatim.
.\run_evals.ps1 -Regenerate

# 2. YOU label 25 answers, blind. ~20 minutes. No judge has run yet.
.\run_evals.ps1 -Label

# 3. Check the seal is intact
.\run_evals.ps1 -Status

# 4. Judge v1 -> agreement_before -> judge_v2 from its own mistakes -> agreement_after
.\run_evals.ps1 -Agreement

# 5. The one-command eval table, pass rate by mode
.\run_evals.ps1
```

**Why the order is enforced:** `agreement.py` refuses to start if `labels_25.json` is missing, and refuses again if the file's SHA256 no longer matches the sealed receipt. So you cannot run the judge, see its verdicts, and then write labels that agree with it. That is what the 25 marks are actually testing.

---

## 2. What to show your mentor

**1. The eval set, by mode** — `evaluation/week6/eval_set.json`
Point at `reg_source_label_leak`. Read its `origin` field out loud: a real trace id and timestamp from `logs/ask_traces.jsonl`.
> "This is a real failure from my own app, replayed word for word. It is never regenerated, so if that bug comes back the test goes red."

**2. The assertion split** — `app/week6_assertions.py`
> "Four criteria used to be in the judge prompt. They are now `if` statements. Checking whether 'Section 2.3' is a real clause is a dictionary lookup — paying a model for that is paying for something that can have an off day."

Show the printed counts at the bottom of `.\run_evals.ps1`: **9 assertions (4 moved out), 1 judged criterion.**

**3. The judge prompt** — `evaluation/week6/judge_v1.txt`
Show the `DO NOT GRADE` block.
> "Moving a criterion means deleting it from the prompt, not just adding a rule elsewhere. If I left it in both places I would be double-counting it."

**4. The seal** — `.\run_evals.ps1 -Status`
> "This hash proves my 25 labels existed before the judge ran. If I edited them afterwards, the hash would not match and the agreement command would refuse to give me a number."

**5. The before → after** — from step 4's output, and `course/results/week6_agreement.json`
Show `agreement_before`, then `judge_v2.txt` with the two worked examples in it, then `agreement_after`.
> "The two examples are cases the judge itself got wrong. I did not pick cases that flattered it."

**6. The per-mode table** — from step 5
> "I never report one overall number. An average hides a regression in one mode while easy modes carry it."

---

## 3. What to explain (two sentences each)

**Why validate a judge at all?**
An AI judge I never checked is just a confident number. If it disagrees with me, its score is meaningless no matter how fluent its explanation is.

**What does "blind" mean here?**
I labelled from the question and the answer only, before any judge verdict existed. Reading the judge first and then labelling is agreeing with myself with extra steps.

**Why binary pass/fail and not 1–10?**
Because I need a decision: trust the score or do not. A small model cannot reliably tell a 6 from a 7, and a "within 1 is a match" tolerance would inflate agreement into meaninglessness.

**Why move criteria into assertions?**
They are free, instant and never inconsistent. It also makes the judge's job smaller, which makes it easier to validate — one criterion is testable, five tangled ones are not.

**What is the acceptance rule?**
At least 80% overall agreement **and** at least 80% on the answers I failed, with both classes present. The second half matters: a judge that passes everything scores 100% against an all-pass label set and is worthless.

**Why iterate using the judge's own disagreements?**
Because those are its actual errors. Choosing nicer examples by hand would tune it to look better without fixing the boundary it gets wrong.

---

## 4. Mentor cross-check questions and answers

**Q: Prove your labels predate the judge run.**
`evaluation/week6/labels_receipt.json` holds the labels' SHA256 and an ISO timestamp. `agreement.py` re-hashes the label file at run time and aborts if it changed. The judge run's own timestamps are in `course/results/week6_agreement.json`, after the sealed time. There is no git repo here, so the hash-plus-timestamp seal is the ordering evidence, which the task accepts.

**Q: How do I know you did not just relabel the ones you disagreed on?**
You would see it: the receipt hash would not match, and the agreement command refuses to produce a number in that state. That refusal is the point — the tool will not let me move the ruler instead of the thing being measured.

**Q: Which criteria did you move, and are they really gone from the judge?**
Four: section reference resolves, handbook version cited, notice figure is numeric, out-of-jurisdiction refusal. They appear in `judge_v1.txt` only under `DO NOT GRADE`, and a unit test asserts each phrase sits after that heading, so they cannot silently creep back.

**Q: How many assertions versus judged criteria?**
9 deterministic assertions, of which 4 were moved out of the judge. 1 criterion is left for the judge. Printed by `.\run_evals.ps1`, computed from the code, not typed into a slide.

**Q: Why does your app now cite a section and a version — did you just make the assertions easy?**
Fair challenge. Python derives both from the retrieved chunk (`attribute()` in `app/answer_quality.py`); the model is never asked for them, so they cannot be hallucinated. That does make those two assertions pass by construction on live answers — and they still **fail on the frozen regressions**, which is what a regression guard is for. A test pins exactly that.

**Q: Are the regressions genuinely verbatim?**
Yes. `reg_source_label_leak` is trace `8f47ac02…` from 2026-09-03, answer copied character for character, including the leaked `SOURCE=leave-policy.txt`. Regression cases have `kind: regression` and are scored as-is, never re-answered.

**Q: Was your prediction right?**
See `prediction.txt` and section 6 below. I predicted the judge's errors would be mostly false FAILs on correct-but-terse answers. I score that honestly against what the disagreements actually were.

**Q: What are the limits of this?**
25 labels from one labeller — me. There is no second human to adjudicate disagreements, so "agreement" means the judge matches *my* reading, not that either of us is right. The same model family generates and judges, so they can share blind spots. And a high pass rate on 33 cases is not a claim about all HR questions.

---

## 5. Results — pass rate by mode

<!-- MODE TABLE -->

---

## 6. Results — judge agreement, and the prediction scored

<!-- AGREEMENT -->

---

## 7. Submission checklist

| Required | File | Status |
|---|---|---|
| `labels_25.json` with proof it predates the judge | `evaluation/week6/labels_25.json` + `labels_receipt.json` | **you must run `-Label`** |
| `judge_v1.txt` and `judge_v2.txt`, diffed, 2 examples visible in v2 | `evaluation/week6/` | v1 ready; v2 written by `-Agreement` |
| `prediction.txt` written before iterating | `evaluation/week6/prediction.txt` | done |
| One-command eval output, pass rate by mode | `.\run_evals.ps1` | done |
| `agreement_before` / `agreement_after` | `course/results/week6_agreement.json` | needs your labels |
| Assertion count vs judged criteria count | printed by `.\run_evals.ps1` | done (9 / 1) |
| 2+ disagreements read, verdict on who was right | `week6_agreement.json` → `disagreements` | needs your labels |

---

## 8. Common mistakes, and how we avoid each one

The task set lists five. Here is our answer to each:

| Mistake | How this build avoids it |
|---|---|
| Running the judge first, then writing labels | `agreement.py` exits if labels are missing, and re-checks the seal |
| Reaching 85% by relabelling disagreements | Editing labels breaks the hash and the run refuses |
| Paying a model to check a section reference resolves | It is a dict lookup in `app/handbook.py` |
| Scoring 1–10 and calling within-1 a match | The judge returns a boolean; no numeric score exists |
| Reporting one overall pass rate | The per-mode table prints first; overall prints last |
