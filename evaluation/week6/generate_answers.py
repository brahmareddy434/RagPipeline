"""Produce the answers that get graded: once, saved, then never regenerated.

    python -m evaluation.week6.generate_answers

Live cases are answered by the current app against the handbook. Regression cases are NOT
regenerated: their recorded answer is copied in verbatim from the real failed trace, which
is the whole point of a regression case.

The output file is the input to both the blind labelling step and the judge, so both grade
exactly the same text. Writing it once is what makes the comparison fair.
"""
import asyncio
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from app.legacy import handbook
from app.config.settings import get_settings
from app.bootstrap import Container
from app.schemas import RetrievalOptions

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "evaluation" / "week6"
EVAL_SET = HERE / "eval_set.json"
ANSWERS = HERE / "answers.json"


async def main() -> int:
    data = json.loads(EVAL_SET.read_text(encoding="utf-8"))
    cases = data["cases"]
    settings = get_settings().model_copy(update={"collection_name": "week6_handbook"})
    container = Container.build(settings)
    try:
        await container.ingestion.ingest(handbook.files())
        rows = []
        for index, case in enumerate(cases, 1):
            if case["kind"] == "regression":
                rows.append({"id": case["id"], "mode": case["mode"], "kind": "regression",
                             "question": case["question"], "answer": case["frozen_answer"],
                             "abstained": False, "citations": [], "validation_issues": [],
                             "origin": case["origin"], "latency_ms": 0.0})
                print(f"{index:>2}/{len(cases)} {case['id']:<34} replayed verbatim", flush=True)
                continue
            result = await container.rag.answer(case["question"], 0, 4, RetrievalOptions(k=4))
            payload = result.model_dump(mode="json")
            rows.append({"id": case["id"], "mode": case["mode"], "kind": "live",
                         "question": case["question"], "answer": payload["answer"],
                         "abstained": payload["abstained"],
                         "citations": [{"source": c["source"], "clause": c.get("clause", ""),
                                        "number": c["number"]} for c in payload["citations"]],
                         "validation_issues": payload["validation_issues"],
                         "latency_ms": None})
            print(f"{index:>2}/{len(cases)} {case['id']:<34} "
                  f"{'refused' if payload['abstained'] else 'answered'}", flush=True)
        body = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "eval_set_sha256": hashlib.sha256(EVAL_SET.read_bytes()).hexdigest(),
            "handbook_version": handbook.VERSION,
            "corpus_sha256": container.store.fingerprint(),
            "chat_model": container.ollama.chat_model,
            "embedding_model": container.ollama.embed_model,
            "answers": rows,
        }
        body["answers_sha256"] = hashlib.sha256(
            json.dumps(rows, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        ANSWERS.write_text(json.dumps(body, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nwrote {ANSWERS.relative_to(ROOT)}  ({len(rows)} answers)")
        print(f"answers_sha256 {body['answers_sha256']}")
        return 0
    finally:
        await container.ollama.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
