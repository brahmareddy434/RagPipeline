"""Week 7 Task Set C: race the HR agent against the fixed workflow.

    python -m course.race                 # both systems, 10 questions
    python -m course.race --repeats 2      # repeat each question
    python -m course.race --only agent
    python -m course.race --budget-demo    # force a clean budget termination and log it

Reports the four numbers the task set asks for, per system:

    pass rate        deterministic assertions, declared in course/week7_questions.json
                     BEFORE any run
    p50 latency      median wall clock per question (not the mean: the tail is the agent's
                     problem and the median is what a user feels)
    total tokens     prompt + completion, SUMMED OVER EVERY LAP. The loop re-sends the whole
                     message list each lap, so counting only the final call would understate
                     the agent by multiples. app/ollama_client.py records every HTTP call
                     into a ContextVar, and the agent sums all of them.
    cost/question    those tokens at the reference rate in app/models.py. Local inference is
                     free, so this is a modelled cost; only the ratio is meaningful.

Writes course/results/race.csv (8 numbers) and course/results/week7_race.json (full rows).
"""
import argparse
import asyncio
import csv
import hashlib
import json
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

from app.legacy import handbook
from app.config.settings import get_settings
from app.bootstrap import Container
from app.schemas import AgentBudget, RetrievalOptions

from app.config.paths import PROJECT_ROOT as ROOT
OUT = ROOT / "course" / "results"
QUESTION_FILE = ROOT / "course" / "week7_questions.json"
QUESTIONS = json.loads(QUESTION_FILE.read_text(encoding="utf-8"))["questions"]


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_json(name: str, data: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


async def build(collection: str = "course_week7_handbook"):
    """Index the versioned handbook, not the Week 3-5 corpus."""
    settings = get_settings().model_copy(update={"collection_name": collection})
    container = Container.build(settings)
    try:
        await container.ingestion.ingest(handbook.files())
        return container
    except BaseException:
        await container.ollama.close()
        raise


def score(question: dict, run: dict) -> dict:
    """Deterministic assertions only. No judge decides the race."""
    answer = run["answer"]
    lowered = answer.casefold()
    abstained = bool(run.get("abstained"))
    checks = {
        "correct_abstention": abstained if question["expect_abstention"] else not abstained,
        "required_facts_present": question["expect_abstention"]
                                  or all(f.casefold() in lowered for f in question["required_facts"]),
        "forbidden_facts_absent": not any(f.casefold() in lowered for f in question["forbidden_facts"]),
        "evidence_validated": not run.get("validation_issues"),
    }
    return {"checks": checks, "pass": all(checks.values())}


def numbers(rows: list[dict]) -> dict:
    """The four numbers the rubric wants, plus the context needed to read them."""
    if not rows:
        return {}
    latencies = [r["usage"]["latency_ms"] for r in rows]
    return {
        "questions": len(rows),
        "pass_rate": round(sum(r["score"]["pass"] for r in rows) / len(rows), 4),
        "p50_latency_ms": round(statistics.median(latencies), 1),
        "total_tokens": sum(r["usage"]["total_tokens"] for r in rows),
        "cost_per_question_usd": round(statistics.fmean(r["usage"]["cost_usd"] for r in rows), 8),
        "mean_latency_ms": round(statistics.fmean(latencies), 1),
        "p90_latency_ms": round(sorted(latencies)[max(0, int(len(latencies) * 0.9) - 1)], 1),
        "mean_model_calls": round(statistics.fmean(r["usage"]["model_calls"] for r in rows), 2),
        "pass_rate_branching": _rate(rows, True),
        "pass_rate_non_branching": _rate(rows, False),
        "abstentions": sum(r["abstained"] for r in rows),
    }


def _rate(rows: list[dict], branching: bool) -> float | None:
    subset = [r for r in rows if r["branching"] is branching]
    return round(sum(r["score"]["pass"] for r in subset) / len(subset), 4) if subset else None


def write_csv(report: dict) -> Path:
    """race.csv: the eight numbers, four per system, in one comparable table."""
    path = OUT / "race.csv"
    fields = ["system", "questions", "pass_rate", "p50_latency_ms", "total_tokens",
              "cost_per_question_usd", "pass_rate_branching", "pass_rate_non_branching",
              "mean_model_calls"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for system in ("agent", "workflow"):
            stats = report.get(system)
            if stats:
                writer.writerow({"system": system, **{f: stats.get(f) for f in fields[1:]}})
    return path


async def race(repeats: int, only: str | None, budget: AgentBudget) -> dict:
    container = await build()
    report = {
        "task_set": "Week 7 Practical — Task Set C (HR policy)",
        "started_at": timestamp(), "repeats": repeats,
        "questions_sha256": hashlib.sha256(QUESTION_FILE.read_bytes()).hexdigest(),
        "corpus_sha256": container.store.fingerprint(),
        "handbook_version": handbook.VERSION,
        "configuration": {
            "chat_model": container.ollama.chat_model,
            "embedding_model": container.ollama.embed_model,
            "temperature": 0, "retrieval": RetrievalOptions().model_dump(),
            "budget": budget.model_dump(),
            "execution": "sequential; one local Ollama runner, so concurrent runs would distort latency",
            "token_accounting": "every HTTP call in the run is summed, not just the final one",
        },
        "questions": QUESTIONS,
        "rows": {"agent": [], "workflow": []},
    }
    save_json("week7_race.json", report)
    try:
        for repeat in range(1, repeats + 1):
            for question in QUESTIONS:
                for system in ("agent", "workflow"):
                    if only and only != system:
                        continue
                    started = time.perf_counter()
                    try:
                        result = (await container.agent.run(question["question"], None, budget)
                                  if system == "agent" else
                                  await container.workflow.run(question["question"]))
                        run = result.model_dump(mode="json")
                        run["error"] = None
                    except Exception as exc:
                        run = {"answer": "", "citations": [], "abstained": False, "steps": [],
                               "validation_issues": [f"run failed: {exc}"],
                               "error": f"{type(exc).__name__}: {exc}",
                               "usage": {"latency_ms": round((time.perf_counter() - started) * 1000, 2),
                                         "total_tokens": 0, "cost_usd": 0.0, "model_calls": 0, "steps": 0}}
                    row = {"repeat": repeat, "id": question["id"], "branching": question["branching"],
                           "question": question["question"], "answer": run["answer"],
                           "cited_sources": sorted({c["source"] for c in run.get("citations", [])}),
                           "abstained": run.get("abstained", False),
                           "validation_issues": run.get("validation_issues", []),
                           "stop_reason": run.get("stop_reason"),
                           "tools_used": [s.get("tool") or s.get("stage") for s in run.get("steps", [])],
                           "usage": run["usage"], "error": run["error"],
                           "score": score(question, run), "timestamp": timestamp()}
                    report["rows"][system].append(row)
                    save_json("week7_race.json", report)
                    print(f"r{repeat} {system:<9} {question['id']:<24} "
                          f"pass={str(row['score']['pass']):<5} "
                          f"{row['usage']['latency_ms']:>7.0f}ms {row['usage']['total_tokens']:>5}tok "
                          f"${row['usage']['cost_usd']:.6f} {row['usage'].get('steps', 0)} steps",
                          flush=True)

        for system in ("agent", "workflow"):
            report[system] = numbers(report["rows"][system])
        if report.get("agent") and report.get("workflow"):
            a, w = report["agent"], report["workflow"]
            report["comparison"] = {
                "pass_rate_delta": round(a["pass_rate"] - w["pass_rate"], 4),
                "p50_latency_ratio_agent_over_workflow": round(
                    a["p50_latency_ms"] / max(w["p50_latency_ms"], 1e-9), 2),
                "token_ratio_agent_over_workflow": round(
                    a["total_tokens"] / max(w["total_tokens"], 1), 2),
                "cost_ratio_agent_over_workflow": round(
                    a["cost_per_question_usd"] / max(w["cost_per_question_usd"], 1e-12), 2),
                "branching_pass_delta": (
                    None if a["pass_rate_branching"] is None or w["pass_rate_branching"] is None
                    else round(a["pass_rate_branching"] - w["pass_rate_branching"], 4)),
            }
        report["completed_at"] = timestamp()
        save_json("week7_race.json", report)
        csv_path = write_csv(report)
        print_summary(report, csv_path)
        return report
    finally:
        await container.ollama.close()


def print_summary(report: dict, csv_path: Path) -> None:
    a, w = report.get("agent"), report.get("workflow")
    print("\n" + "=" * 78)
    print(f"Week 7 race — {report['configuration']['chat_model']} — handbook {report['handbook_version']}")
    print("=" * 78)
    if not (a and w):
        print("Only one system was run; no comparison.")
        return
    print(f"{'number':<30}{'agent':>16}{'fixed workflow':>18}")
    def line(label, fmt):
        print(f"{label:<30}{fmt(a):>16}{fmt(w):>18}")
    line("pass rate", lambda s: f"{s['pass_rate']:.0%}")
    line("p50 latency", lambda s: f"{s['p50_latency_ms'] / 1000:.1f} s")
    line("total tokens", lambda s: f"{s['total_tokens']:,}")
    line("cost per question", lambda s: f"${s['cost_per_question_usd']:.6f}")
    print("-" * 78)
    line("pass rate, branching", lambda s: "n/a" if s["pass_rate_branching"] is None
         else f"{s['pass_rate_branching']:.0%}")
    line("pass rate, non-branching", lambda s: "n/a" if s["pass_rate_non_branching"] is None
         else f"{s['pass_rate_non_branching']:.0%}")
    line("mean model calls", lambda s: f"{s['mean_model_calls']:.2f}")
    c = report["comparison"]
    print("-" * 78)
    print(f"agent / workflow: {c['p50_latency_ratio_agent_over_workflow']}x p50 latency, "
          f"{c['token_ratio_agent_over_workflow']}x tokens, {c['cost_ratio_agent_over_workflow']}x cost")
    print(f"pass-rate delta (agent - workflow): {c['pass_rate_delta']:+.0%}"
          + (f"; on branching questions only: {c['branching_pass_delta']:+.0%}"
             if c["branching_pass_delta"] is not None else ""))
    print(f"\nrace.csv: {csv_path}")
    print("full rows: course/results/week7_race.json")


async def budget_demo(which: str = "max_steps") -> dict:
    """Force one budget to fire and save the log, as the task set requires.

    The point is that the run terminates cleanly and says which ceiling fired - it does not
    spin, and it does not crash. It still returns the best grounded answer it gathered.
    """
    container = await build()
    budgets = {
        "max_steps": AgentBudget(max_steps=2),
        "max_tokens": AgentBudget(max_steps=8, max_tokens=900),
        "max_cost_usd": AgentBudget(max_steps=8, max_cost_usd=0.0004),
        "max_seconds": AgentBudget(max_steps=8, max_seconds=20.0),
    }
    budget = budgets[which]
    question = ("EMP-1007 wants to take 6 days of planned leave. "
                "How many working days notice must they give?")
    try:
        started = time.perf_counter()
        result = await container.agent.run(question, None, budget)
        log = {
            "demonstrates": f"clean termination on {which}",
            "started_at": timestamp(),
            "question": question,
            "budget_applied": budget.model_dump(),
            "stop_reason": result.stop_reason,
            "stop_detail": result.stop_detail,
            "completed": result.completed,
            "which_budget_fired": result.stop_reason,
            "steps": [{"index": s["index"], "tool": s["tool"], "arguments": s["arguments"],
                       "ok": s["ok"], "latency_ms": s["latency_ms"],
                       "prompt_tokens": s["prompt_tokens"], "completion_tokens": s["completion_tokens"],
                       "observation": s["observation"][:300]} for s in result.steps],
            "usage": result.usage,
            "answer_after_termination": result.answer,
            "abstained": result.abstained,
            "wall_clock_s": round(time.perf_counter() - started, 2),
            "reading": ("The loop stopped because the named budget was exceeded, reported which one, "
                        "and still produced an answer from the evidence already gathered. "
                        "completed=false marks it as not self-terminated, so it must not be trusted silently."),
        }
        save_json("week7_budget_termination.json", log)
        print(json.dumps({k: v for k, v in log.items() if k != "steps"}, indent=2))
        print(f"\nsteps taken: {len(log['steps'])}")
        for s in log["steps"]:
            print(f"  {s['index']}. {s['tool']}({json.dumps(s['arguments'])}) ok={s['ok']}")
        print("\nsaved: course/results/week7_budget_termination.json")
        return log
    finally:
        await container.ollama.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Week 7 Task Set C: agent vs fixed workflow")
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--only", choices=["agent", "workflow"], default=None)
    parser.add_argument("--max-steps", type=int, default=6)
    parser.add_argument("--max-seconds", type=float, default=180.0)
    parser.add_argument("--max-tokens", type=int, default=16000)
    parser.add_argument("--max-cost-usd", type=float, default=0.02)
    parser.add_argument("--budget-demo", nargs="?", const="max_steps",
                        choices=["max_steps", "max_tokens", "max_cost_usd", "max_seconds"])
    args = parser.parse_args()
    if args.budget_demo:
        asyncio.run(budget_demo(args.budget_demo))
        return 0
    budget = AgentBudget(max_steps=args.max_steps, max_seconds=args.max_seconds,
                         max_tokens=args.max_tokens, max_cost_usd=args.max_cost_usd)
    asyncio.run(race(args.repeats, args.only, budget))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
