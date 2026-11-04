"""The one command: score every case and print pass rate BY MODE.

    python -m evaluation.week6.run_evals             # score the saved answers
    python -m evaluation.week6.run_evals --regenerate # answer the live cases first, then score
    python -m evaluation.week6.run_evals --check      # exit non-zero if any mode is below 100%

Only deterministic assertions run here. The judge is a separate command
(evaluation/week6/agreement.py), because the assertions are free and the judge is not, and
because mixing them would hide which layer made a decision.

One overall pass rate is deliberately not the headline. An average will happily hide a
regression on the incomplete_conditions mode while easy citation cases carry the number, so
the per-mode table is printed first and the overall figure last.
"""
import argparse
import asyncio
import json
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from app.week6_assertions import run_assertions, split_counts

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "evaluation" / "week6"
OUT = ROOT / "course" / "results"
EVAL_SET = HERE / "eval_set.json"
ANSWERS = HERE / "answers.json"


def score_all() -> dict:
    data = json.loads(EVAL_SET.read_text(encoding="utf-8"))
    cases = {c["id"]: c for c in data["cases"]}
    if not ANSWERS.exists():
        sys.exit("No answers.json. Run: python -m evaluation.week6.run_evals --regenerate")
    body = json.loads(ANSWERS.read_text(encoding="utf-8"))

    rows = []
    for answer in body["answers"]:
        case = cases[answer["id"]]
        result = run_assertions(answer["answer"], case)
        rows.append({"id": answer["id"], "mode": case["mode"], "kind": case["kind"],
                     "question": case["question"], "answer": answer["answer"],
                     "assertions": result["checks"], "skipped": result["skipped"],
                     "pass": result["pass"],
                     "failed_assertions": [k for k, v in result["checks"].items() if not v]})

    by_mode = defaultdict(list)
    for row in rows:
        by_mode[row["mode"]].append(row)
    modes = {mode: {"cases": len(items),
                    "pass": sum(r["pass"] for r in items),
                    "pass_rate_percent": round(sum(r["pass"] for r in items) / len(items) * 100, 1),
                    "failing": [r["id"] for r in items if not r["pass"]]}
             for mode, items in sorted(by_mode.items())}
    regressions = [r for r in rows if r["kind"] == "regression"]
    return {
        "task_set": data["task_set"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "answers_generated_at": body["generated_at"],
        "chat_model": body.get("chat_model"),
        "handbook_version": body.get("handbook_version"),
        "cases": len(rows),
        "split": split_counts(),
        "per_mode": modes,
        "overall_pass_rate_percent": round(sum(r["pass"] for r in rows) / len(rows) * 100, 1),
        "regression_cases": len(regressions),
        "regression_pass_rate_percent": round(
            sum(r["pass"] for r in regressions) / len(regressions) * 100, 1) if regressions else None,
        "rows": rows,
    }


def print_report(report: dict) -> None:
    split = report["split"]
    print(f"\nWeek 6 evals — {report['task_set']}")
    print(f"handbook {report['handbook_version']}  model {report['chat_model']}  "
          f"{report['cases']} cases\n")
    print(f"{'mode':<26}{'cases':>7}{'pass':>7}{'rate':>9}")
    print("-" * 49)
    for mode, stats in report["per_mode"].items():
        print(f"{mode:<26}{stats['cases']:>7}{stats['pass']:>7}{stats['pass_rate_percent']:>8.1f}%")
    print("-" * 49)
    print(f"{'OVERALL':<26}{report['cases']:>7}"
          f"{sum(m['pass'] for m in report['per_mode'].values()):>7}"
          f"{report['overall_pass_rate_percent']:>8.1f}%")
    print(f"\nregression cases replayed verbatim: {report['regression_cases']}"
          f" (pass rate {report['regression_pass_rate_percent']}%)")
    print(f"\nassertion / judge split")
    print(f"  deterministic assertions : {split['assertions_total']}"
          f"  (of which {split['assertions_moved_out_of_judge']} were moved out of the judge)")
    print(f"  criteria left to the judge: {split['judged_criteria']}")
    for criterion in split["moved_criteria"]:
        print(f"    moved out: {criterion}")
    for criterion in split["remaining_judged_criteria"]:
        print(f"    judged   : {criterion}")
    failing = {m: s["failing"] for m, s in report["per_mode"].items() if s["failing"]}
    if failing:
        print("\nfailing cases by mode")
        for mode, ids in failing.items():
            print(f"  {mode}: {', '.join(ids)}")
        reasons = defaultdict(list)
        for row in report["rows"]:
            for name in row["failed_assertions"]:
                reasons[name].append(row["id"])
        print("\nwhich assertion failed, and where")
        for name, ids in sorted(reasons.items(), key=lambda kv: -len(kv[1])):
            print(f"  {name:<28} {len(ids)} case(s): {', '.join(ids[:6])}"
                  + (" ..." if len(ids) > 6 else ""))
    print(f"\nfull evidence: course/results/week6_evals.json")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--regenerate", action="store_true",
                        help="answer the live cases with the current app before scoring")
    parser.add_argument("--check", action="store_true",
                        help="exit non-zero if any mode is below 100%%")
    args = parser.parse_args()
    if args.regenerate:
        code = subprocess.call([sys.executable, "-m", "evaluation.week6.generate_answers"], cwd=ROOT)
        if code:
            return code
    report = score_all()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "week6_evals.json").write_text(json.dumps(report, indent=2, ensure_ascii=False),
                                          encoding="utf-8")
    print_report(report)
    if args.check:
        weak = [m for m, s in report["per_mode"].items() if s["pass_rate_percent"] < 100]
        if weak:
            print(f"\nFAIL: modes below 100%: {', '.join(weak)}")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
