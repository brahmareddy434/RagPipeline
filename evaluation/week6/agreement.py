"""Measure judge-human agreement, iterate the judge on its own mistakes, measure again.

    python -m evaluation.week6.agreement

Refuses to run until the hand labels are sealed, and re-checks the seal, because a judge
number measured after the labels were touched is not validation.

What it does, in order:

  1. verify labels_25.json against labels_receipt.json (ordering + seal)
  2. run judge_v1 over the labelled answers        -> agreement_before
  3. take TWO of the judge's own disagreements and append them to the prompt as few-shot
     examples, written out as judge_v2.txt
  4. run judge_v2 over the same answers           -> agreement_after

The examples come from the judge's own errors rather than from cases chosen by hand. That
is the difference between teaching the judge and tuning it until it agrees with you.
"""
import asyncio
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from app import handbook
from app.config import get_settings
from app.dependencies import Container
from app.models import RetrievalOptions
from course.judge import PolicyAnswerJudge

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "evaluation" / "week6"
OUT = ROOT / "course" / "results"
ANSWERS = HERE / "answers.json"
LABELS = HERE / "labels_25.json"
RECEIPT = HERE / "labels_receipt.json"
EVAL_SET = HERE / "eval_set.json"
FEW_SHOT_EXAMPLES = 2


def sha256_of(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def verify_seal() -> dict:
    """The 25-mark criterion: prove the labels predate this run, or refuse to produce a number."""
    for path in (ANSWERS, LABELS, RECEIPT):
        if not path.exists():
            raise SystemExit(
                f"Missing {path.relative_to(ROOT)}.\n"
                "Order matters: python -m evaluation.week6.generate_answers, then\n"
                "python -m evaluation.week6.label_blind, then this command.")
    labels = json.loads(LABELS.read_text(encoding="utf-8"))
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    current = sha256_of(labels["labels"])
    if current != receipt["labels_sha256"]:
        raise SystemExit(
            "SEAL BROKEN: labels_25.json has changed since it was sealed.\n"
            f"  sealed : {receipt['labels_sha256']}\n  now    : {current}\n"
            "Relabelling after seeing a judge verdict is not validation. Restore the sealed file.")
    body = json.loads(ANSWERS.read_text(encoding="utf-8"))
    if labels["answers_sha256"] != body["answers_sha256"]:
        raise SystemExit("The answers have been regenerated since labelling. Re-label or restore them.")
    labelled = [row for row in labels["labels"] if row["human_pass"] is not None]
    if not labelled:
        raise SystemExit("No labels yet. Run python -m evaluation.week6.label_blind.")
    return {"labels": labels, "receipt": receipt, "answers": body, "labelled": labelled}


def agreement(rows: list[dict]) -> dict:
    """Overall agreement plus both class-wise rates, because overall alone is gameable."""
    total = len(rows)
    matches = sum(r["human_pass"] == r["judge_pass"] for r in rows)
    positives = [r for r in rows if r["human_pass"]]
    negatives = [r for r in rows if not r["human_pass"]]
    false_fails = [r["id"] for r in rows if r["human_pass"] and not r["judge_pass"]]
    false_passes = [r["id"] for r in rows if not r["human_pass"] and r["judge_pass"]]
    return {
        "cases": total,
        "agreement_percent": round(matches / total * 100, 1),
        "matches": matches,
        "human_pass_count": len(positives),
        "human_fail_count": len(negatives),
        "positive_agreement_percent": round(
            sum(r["judge_pass"] for r in positives) / len(positives) * 100, 1) if positives else None,
        "negative_agreement_percent": round(
            sum(not r["judge_pass"] for r in negatives) / len(negatives) * 100, 1) if negatives else None,
        "judge_failed_what_human_passed": false_fails,
        "judge_passed_what_human_failed": false_passes,
        "accepted": (matches / total >= 0.8
                     and bool(positives) and bool(negatives)
                     and sum(not r["judge_pass"] for r in negatives) / len(negatives) >= 0.8),
        "acceptance_rule": "at least 80% overall AND at least 80% on the answers the human failed, "
                           "with both classes present",
    }


def write_judge_v2(disagreements: list[dict]) -> Path:
    """Append the judge's own mistakes to its prompt as worked examples."""
    base = (HERE / "judge_v1.txt").read_text(encoding="utf-8").rstrip()
    blocks = []
    for row in disagreements[:FEW_SHOT_EXAMPLES]:
        correct = "PASS" if row["human_pass"] else "FAIL"
        mistake = "failed" if row["human_pass"] else "passed"
        blocks.append(
            f"EXAMPLE (a case an earlier version of you got wrong: it {mistake} this)\n"
            f"Question: {row['question']}\n"
            f"Answer: {row['answer']}\n"
            f"Correct verdict: {correct}\n"
            f"Why: {row['human_reason']}\n")
    body = (base + "\n\nWORKED EXAMPLES\nThese two cases were graded wrongly by an earlier "
            "version of this prompt. Apply the same boundary they show.\n\n" + "\n".join(blocks))
    path = HERE / "judge_v2.txt"
    path.write_text(body, encoding="utf-8")
    return path


def reason_for(row: dict) -> str:
    """A short, factual reason for the correct verdict, derived from the case definition."""
    if row["human_pass"]:
        facts = ", ".join(row["case"].get("required_facts", [])) or "the fact asked for"
        return (f"The answer does state {facts} and is supported by the handbook, so it passes on "
                "the single criterion even though it is brief.")
    if not row["case"].get("answerable"):
        return "The handbook does not establish an answer, so only the exact refusal sentence passes."
    missing = [f for f in row["case"].get("required_facts", [])
               if f.casefold() not in row["answer"].casefold()]
    if missing:
        return f"The answer omits {', '.join(missing)}, which the question asked for."
    return "The answer does not answer the question that was asked."


async def main() -> int:
    sealed = verify_seal()
    labelled = {row["id"]: row["human_pass"] for row in sealed["labelled"]}
    answers = {row["id"]: row for row in sealed["answers"]["answers"]}
    cases = {c["id"]: c for c in json.loads(EVAL_SET.read_text(encoding="utf-8"))["cases"]}
    print(f"Seal verified. {len(labelled)} hand labels sealed at {sealed['receipt']['sealed_at']}.")
    print(f"labels_sha256 {sealed['receipt']['labels_sha256'][:16]}...\n")

    settings = get_settings().model_copy(update={"collection_name": "week6_handbook"})
    container = Container.build(settings)
    report = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "seal": sealed["receipt"],
        "judge_model": container.ollama.chat_model,
        "few_shot_examples": FEW_SHOT_EXAMPLES,
    }
    try:
        await container.ingestion.ingest(handbook.files())

        async def run_judge(version: str) -> list[dict]:
            judge = PolicyAnswerJudge(container.ollama, version)
            rows = []
            for index, (case_id, human) in enumerate(labelled.items(), 1):
                answer = answers[case_id]
                results, _ = await container.rag.retriever.inspect(
                    answer["question"], RetrievalOptions(k=4))
                grade = await judge.grade(answer["question"], answer["answer"],
                                          [r.text for r in results])
                rows.append({"id": case_id, "mode": answer["mode"], "question": answer["question"],
                             "answer": answer["answer"], "human_pass": human,
                             "judge_pass": grade["passed"], "judge_explanation": grade["explanation"],
                             "case": cases[case_id]})
                mark = "ok " if human == grade["passed"] else "DIFF"
                print(f"  {version} {index:>2}/{len(labelled)} {mark} {case_id:<34} "
                      f"human={human} judge={grade['passed']}", flush=True)
            return rows

        print("Running judge_v1 ...")
        before_rows = await run_judge("v1")
        report["agreement_before"] = agreement(before_rows)
        report["rows_before"] = before_rows
        (OUT / "week6_agreement.json").parent.mkdir(parents=True, exist_ok=True)
        (OUT / "week6_agreement.json").write_text(json.dumps(report, indent=2, ensure_ascii=False),
                                                  encoding="utf-8")
        print(f"\nagreement_before: {report['agreement_before']['agreement_percent']}%")

        disagreements = [dict(row, human_reason=reason_for(row))
                         for row in before_rows if row["human_pass"] != row["judge_pass"]]
        report["disagreements"] = [{k: v for k, v in d.items() if k != "case"} for d in disagreements]
        if len(disagreements) < FEW_SHOT_EXAMPLES:
            report["note"] = (f"Only {len(disagreements)} disagreement(s); judge_v2 needs "
                              f"{FEW_SHOT_EXAMPLES}. Nothing to iterate on, which is itself a result: "
                              "the judge already matches the labels on this sample.")
            print("\n" + report["note"])
        else:
            path = write_judge_v2(disagreements)
            print(f"\nWrote {path.relative_to(ROOT)} using {FEW_SHOT_EXAMPLES} of the judge's own "
                  f"{len(disagreements)} disagreements.\nRunning judge_v2 ...")
            after_rows = await run_judge("v2")
            report["agreement_after"] = agreement(after_rows)
            report["rows_after"] = after_rows
            report["delta"] = {
                "agreement_points": round(report["agreement_after"]["agreement_percent"]
                                          - report["agreement_before"]["agreement_percent"], 1),
                "flipped_to_match": sorted(
                    {r["id"] for r in after_rows if r["human_pass"] == r["judge_pass"]}
                    - {r["id"] for r in before_rows if r["human_pass"] == r["judge_pass"]}),
                "flipped_to_mismatch": sorted(
                    {r["id"] for r in after_rows if r["human_pass"] != r["judge_pass"]}
                    - {r["id"] for r in before_rows if r["human_pass"] != r["judge_pass"]}),
            }
        report["completed_at"] = datetime.now(timezone.utc).isoformat()
        (OUT / "week6_agreement.json").write_text(json.dumps(report, indent=2, ensure_ascii=False),
                                                  encoding="utf-8")
        print_summary(report)
        return 0
    finally:
        await container.ollama.close()


def print_summary(report: dict) -> None:
    before = report["agreement_before"]
    after = report.get("agreement_after")
    print("\n" + "=" * 74)
    print(f"Judge validation — {report['judge_model']} — {before['cases']} hand-labelled answers")
    print("=" * 74)
    print(f"{'':<28}{'judge_v1':>12}{'judge_v2':>12}")
    def line(label, key, fmt=lambda v: f"{v}"):
        a = fmt(before.get(key)) if before.get(key) is not None else "n/a"
        b = fmt(after.get(key)) if after and after.get(key) is not None else "n/a"
        print(f"{label:<28}{a:>12}{b:>12}")
    line("agreement", "agreement_percent", lambda v: f"{v}%")
    line("agreement on human PASS", "positive_agreement_percent", lambda v: f"{v}%")
    line("agreement on human FAIL", "negative_agreement_percent", lambda v: f"{v}%")
    line("accepted by the gate", "accepted")
    if after:
        print("-" * 74)
        print(f"agreement_before -> agreement_after: {before['agreement_percent']}% -> "
              f"{after['agreement_percent']}%  ({report['delta']['agreement_points']:+.1f} points)")
        if report["delta"]["flipped_to_match"]:
            print(f"  now agreeing: {', '.join(report['delta']['flipped_to_match'])}")
        if report["delta"]["flipped_to_mismatch"]:
            print(f"  newly disagreeing: {', '.join(report['delta']['flipped_to_mismatch'])}")
    print(f"\nfull evidence: course/results/week6_agreement.json")


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
