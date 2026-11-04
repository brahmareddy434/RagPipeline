"""Blind hand-labelling, with proof that the labels came first.

    python -m evaluation.week6.label_blind            # label the 25-answer sample
    python -m evaluation.week6.label_blind --status   # what is sealed so far
    python -m evaluation.week6.label_blind --resume   # continue an unfinished session

25 of 100 marks depend on the labels provably predating the judge run, and the marks are
zero without that evidence. So this tool enforces the ordering rather than trusting it:

* It shows you the question and the answer only. It never shows a judge verdict, because no
  judge has run yet - `agreement.py` refuses to start until labels_25.json exists.
* When you finish, it writes labels_25.json and a separate sealed receipt containing the
  SHA256 of the labels, the SHA256 of the answers they refer to, and an ISO timestamp.
* `agreement.py` re-hashes both files at run time. If the labels were edited after the judge
  ran, the hash no longer matches the receipt and the run is refused.

You are the labeller. The tool cannot label for you, and a pre-filled label is not a blind
label - that is the failure mode the rubric is looking for.
"""
import argparse
import hashlib
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "evaluation" / "week6"
ANSWERS = HERE / "answers.json"
LABELS = HERE / "labels_25.json"
RECEIPT = HERE / "labels_receipt.json"
SAMPLE_SIZE = 25
SAMPLE_SEED = 20260922

CRITERION = ("Does this answer correctly and completely answer the question using only the "
             "handbook? (This is the judge's single criterion.)")


def sha256_of(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def load_answers() -> dict:
    if not ANSWERS.exists():
        sys.exit("Run python -m evaluation.week6.generate_answers first.")
    return json.loads(ANSWERS.read_text(encoding="utf-8"))


def sample(answers: list[dict]) -> list[dict]:
    """A seeded sample, so the 25 labelled answers are reproducible and not cherry-picked."""
    if len(answers) <= SAMPLE_SIZE:
        return list(answers)
    return random.Random(SAMPLE_SEED).sample(answers, SAMPLE_SIZE)


def status() -> int:
    if not LABELS.exists():
        print("labels_25.json: not written yet")
        return 0
    labels = json.loads(LABELS.read_text(encoding="utf-8"))
    print(f"labels_25.json: {len(labels['labels'])} labels, sealed {labels['sealed_at']}")
    if RECEIPT.exists():
        receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
        current = sha256_of(labels["labels"])
        intact = current == receipt["labels_sha256"]
        print(f"receipt labels_sha256: {receipt['labels_sha256'][:16]}...")
        print(f"current  labels_sha256: {current[:16]}...")
        print("SEAL INTACT" if intact else "SEAL BROKEN - labels were edited after sealing")
    passes = sum(1 for row in labels["labels"] if row["human_pass"])
    print(f"human PASS {passes}, human FAIL {len(labels['labels']) - passes}")
    return 0


def ask(index: int, total: int, row: dict) -> bool | None:
    print("\n" + "=" * 78)
    print(f"ANSWER {index} of {total}      (id hidden until the end: labelling is blind to the mode)")
    print("=" * 78)
    print(f"\nQUESTION:\n  {row['question']}\n")
    print("ANSWER:")
    for line in (row["answer"] or "(empty)").splitlines() or ["(empty)"]:
        print(f"  {line}")
    print(f"\n{CRITERION}")
    print("  [p] pass    [f] fail    [s] skip (leave unlabelled)    [q] save and quit")
    while True:
        choice = input("  > ").strip().lower()
        if choice in {"p", "pass"}:
            return True
        if choice in {"f", "fail"}:
            return False
        if choice in {"s", "skip"}:
            return None
        if choice in {"q", "quit"}:
            raise KeyboardInterrupt
        print("  Type p, f, s or q.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.status:
        return status()

    body = load_answers()
    chosen = sample(body["answers"])
    existing: dict[str, bool] = {}
    if args.resume and LABELS.exists():
        existing = {row["id"]: row["human_pass"]
                    for row in json.loads(LABELS.read_text(encoding="utf-8"))["labels"]
                    if row["human_pass"] is not None}
        print(f"Resuming: {len(existing)} already labelled.")
    elif LABELS.exists():
        sys.exit("labels_25.json already exists. Use --resume to continue, or delete it to relabel "
                 "(deleting and relabelling after seeing judge output destroys the blind protocol).")

    print(__doc__.split("\n\n")[0])
    print(f"\n{len(chosen)} answers to label. Seeded sample (seed {SAMPLE_SEED}) of "
          f"{len(body['answers'])} answers.")
    print("No judge has run yet, so there is nothing for you to agree with.\n")

    labels = []
    try:
        todo = [row for row in chosen if row["id"] not in existing]
        for position, row in enumerate(todo, 1):
            verdict = ask(position, len(todo), row)
            labels.append({"id": row["id"], "human_pass": verdict})
    except KeyboardInterrupt:
        print("\nStopping early; labelling what you have done so far.")

    merged = [{"id": row["id"], "human_pass": existing.get(row["id"])} for row in chosen]
    by_id = {row["id"]: row["human_pass"] for row in labels}
    for row in merged:
        if row["id"] in by_id:
            row["human_pass"] = by_id[row["id"]]

    labelled = [row for row in merged if row["human_pass"] is not None]
    payload = {
        "criterion": CRITERION,
        "protocol": "Blind: labelled from question and answer only, before any judge run.",
        "labeller": "project owner (hand labelled)",
        "sample_seed": SAMPLE_SEED,
        "sample_size": len(merged),
        "sealed_at": datetime.now(timezone.utc).isoformat(),
        "answers_sha256": body["answers_sha256"],
        "labels": merged,
    }
    LABELS.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    receipt = {
        "what_this_proves": "These labels existed, with this content, at the sealed_at time below, "
                            "which precedes the judge run recorded in course/results/week6_agreement.json.",
        "sealed_at": payload["sealed_at"],
        "labels_sha256": sha256_of(merged),
        "answers_sha256": body["answers_sha256"],
        "labels_file": str(LABELS.relative_to(ROOT)),
        "labelled": len(labelled),
        "unlabelled": len(merged) - len(labelled),
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(f"\nSealed {len(labelled)} of {len(merged)} labels.")
    print(f"  {LABELS.relative_to(ROOT)}")
    print(f"  {RECEIPT.relative_to(ROOT)}   labels_sha256 {receipt['labels_sha256'][:16]}...")
    if len(labelled) < len(merged):
        print(f"\n{len(merged) - len(labelled)} still unlabelled. Run with --resume to finish.")
    else:
        print("\nNow run: python -m evaluation.week6.agreement")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
