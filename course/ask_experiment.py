"""Measure the /ask answer-precision change. One variable per arm.

    python -m course.ask_experiment            # all three arms, 20 cases
    python -m course.ask_experiment --arms baseline filtered

Arms:
  baseline          all k retrieved chunks go to the model, full 3000-char prompt
  filtered          keep only chunks within keep_ratio of the best match, full prompt
  filtered_compact  same filter, plus the 1500-char compact prompt

Scored with the same deterministic assertions as the Week 6 runner, so the numbers are
comparable with course/results/week6_live.json. Writes course/results/week7_ask_experiment.json.

The complaint this answers: /ask sometimes padded an answer with facts from unrelated
policies. Retrieval returns k chunks whether or not k are relevant, and on this corpus the
filler routinely included injection-example.txt.
"""
import argparse
import asyncio
import hashlib
import json
import statistics
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from app.config.settings import get_settings
from app.bootstrap import Container
from app.schemas import RetrievalOptions
from app.infrastructure.ollama import call_metrics
from app.rag.prompts import PromptBuilder
from app.services import RagService
from course.run import CASES, assertions

from app.config.paths import PROJECT_ROOT as ROOT
OUT = ROOT / "course" / "results"

ARMS = {
    "baseline": {"keep_ratio": 0.0, "cap": 0, "compact": False},
    "filtered": {"keep_ratio": 0.92, "cap": 3, "compact": False},
    "filtered_compact": {"keep_ratio": 0.92, "cap": 3, "compact": True},
}


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def save(name: str, data: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


async def build(collection: str = "course_ask_v1"):
    settings = get_settings().model_copy(update={"collection_name": collection})
    container = Container.build(settings)
    try:
        files = [(p.name, p.read_bytes()) for p in sorted((ROOT / "course" / "corpus").iterdir()) if p.is_file()]
        await container.ingestion.ingest(files)
        return container
    except BaseException:
        await container.ollama.close()
        raise


def aggregate(rows: list[dict]) -> dict:
    by_type = defaultdict(list)
    for row in rows:
        by_type[row["case"]["problem_type"]].append(row)

    def rate(items):
        return round(sum(r["score"]["pass"] for r in items) / len(items), 4)

    return {
        "cases": len(rows),
        "assertion_pass_rate": rate(rows),
        "per_problem_type": {k: {"cases": len(v), "assertion_pass_rate": rate(v)}
                             for k, v in sorted(by_type.items())},
        "mean_latency_ms": round(statistics.fmean(r["latency_ms"] for r in rows), 1),
        "mean_prompt_tokens": round(statistics.fmean(r["prompt_tokens"] for r in rows), 1),
        "mean_total_tokens": round(statistics.fmean(r["total_tokens"] for r in rows), 1),
        "mean_context_chunks": round(statistics.fmean(r["context_chunks"] for r in rows), 2),
        "mean_claims": round(statistics.fmean(r["claims"] for r in rows), 2),
        "abstentions": sum(r["abstained"] for r in rows),
        "injection_doc_in_context": sum(r["injection_doc_in_context"] for r in rows),
    }


async def run(arm_names: list[str]) -> dict:
    container = await build()
    report = {
        "started_at": timestamp(),
        "purpose": "Does filtering weak evidence, and shortening the prompt, make /ask more correct and cheaper?",
        "dataset_sha256": hashlib.sha256((ROOT / "course" / "eval_set.json").read_bytes()).hexdigest(),
        "corpus_sha256": container.store.fingerprint(),
        "configuration": {"chat_model": container.ollama.chat_model,
                          "embedding_model": container.ollama.embed_model,
                          "temperature": 0, "retrieval": RetrievalOptions().model_dump(),
                          "min_relevance": get_settings().min_relevance},
        "arms": {name: ARMS[name] for name in arm_names},
        "rows": {name: [] for name in arm_names},
    }
    save("week7_ask_experiment.json", report)
    try:
        for index, case in enumerate(CASES, 1):
            for name in arm_names:
                arm = ARMS[name]
                service = RagService(container.rag.retriever, container.ollama,
                                     PromptBuilder(compact=arm["compact"]),
                                     get_settings().min_relevance, arm["keep_ratio"], arm["cap"])
                metrics: list[dict] = []
                token = call_metrics.set(metrics)
                started = time.perf_counter()
                try:
                    result = await service.answer(case["question"], 0, 4, RetrievalOptions(k=4))
                    payload = result.model_dump(mode="json")
                    error = None
                except Exception as exc:
                    payload = {"answer": "", "citations": [], "abstained": False, "retrieved": [],
                               "validation_issues": [f"failed: {exc}"], "inspection": {}}
                    error = f"{type(exc).__name__}: {exc}"
                finally:
                    call_metrics.reset(token)
                inspection = payload.get("inspection") or {}
                context_chunks = inspection.get("evidence_selected", len(payload.get("retrieved") or []))
                sources = {r["source"] for r in (payload.get("retrieved") or [])}
                row = {
                    "case": case, "answer": payload["answer"], "abstained": payload.get("abstained", False),
                    "citations": payload.get("citations", []),
                    "cited_sources": [c["source"] for c in payload.get("citations", [])],
                    "claims": len(payload.get("citations", [])),
                    "validation_issues": payload.get("validation_issues", []),
                    "context_chunks": context_chunks,
                    "dropped_sources": inspection.get("dropped_sources", []),
                    "injection_doc_in_context": "injection-example.txt" in sources,
                    "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                    "prompt_tokens": sum(m.get("prompt_eval_count") or 0 for m in metrics),
                    "total_tokens": sum((m.get("prompt_eval_count") or 0) + (m.get("eval_count") or 0)
                                        for m in metrics),
                    "model_calls": len(metrics), "error": error, "timestamp": timestamp(),
                    "score": assertions(case, payload),
                }
                report["rows"][name].append(row)
                save("week7_ask_experiment.json", report)
                print(f"{index:>2}/{len(CASES)} {name:<17} {case['id']:<22} "
                      f"pass={str(row['score']['pass']):<5} ctx={row['context_chunks']} "
                      f"claims={row['claims']} {row['latency_ms']:>7.0f}ms {row['total_tokens']:>5}tok",
                      flush=True)

        for name in arm_names:
            report[name] = aggregate(report["rows"][name])
        if "baseline" in arm_names:
            base = report["baseline"]
            report["delta_vs_baseline"] = {
                name: {
                    "assertion_points": round((report[name]["assertion_pass_rate"] - base["assertion_pass_rate"]) * 100, 1),
                    "latency_percent": round((report[name]["mean_latency_ms"] / base["mean_latency_ms"] - 1) * 100, 1),
                    "total_tokens_percent": round((report[name]["mean_total_tokens"] / base["mean_total_tokens"] - 1) * 100, 1),
                    "prompt_tokens_percent": round((report[name]["mean_prompt_tokens"] / base["mean_prompt_tokens"] - 1) * 100, 1),
                    "per_problem_type_points": {
                        kind: round((report[name]["per_problem_type"][kind]["assertion_pass_rate"]
                                     - base["per_problem_type"][kind]["assertion_pass_rate"]) * 100, 1)
                        for kind in base["per_problem_type"]},
                }
                for name in arm_names if name != "baseline"}
        report["completed_at"] = timestamp()
        save("week7_ask_experiment.json", report)
        print_summary(report, arm_names)
        return report
    finally:
        await container.ollama.close()


def print_summary(report: dict, arm_names: list[str]) -> None:
    print("\n" + "=" * 84)
    print(f"/ask precision experiment - {report['configuration']['chat_model']} - {report['baseline']['cases']} cases")
    print("=" * 84)
    print(f"{'measure':<26}" + "".join(f"{name:>19}" for name in arm_names))
    def line(label, fmt):
        print(f"{label:<26}" + "".join(f"{fmt(report[name]):>19}" for name in arm_names))
    line("assertion pass rate", lambda a: f"{a['assertion_pass_rate']:.0%}")
    line("mean latency", lambda a: f"{a['mean_latency_ms'] / 1000:.1f} s")
    line("mean prompt tokens", lambda a: f"{a['mean_prompt_tokens']:.0f}")
    line("mean total tokens", lambda a: f"{a['mean_total_tokens']:.0f}")
    line("mean context chunks", lambda a: f"{a['mean_context_chunks']:.2f}")
    line("mean claims in answer", lambda a: f"{a['mean_claims']:.2f}")
    line("abstentions", lambda a: str(a["abstentions"]))
    line("injection doc in context", lambda a: str(a["injection_doc_in_context"]))
    print("-" * 84)
    for name, delta in report.get("delta_vs_baseline", {}).items():
        print(f"{name}: {delta['assertion_points']:+.1f} assertion points, "
              f"{delta['latency_percent']:+.1f}% latency, {delta['total_tokens_percent']:+.1f}% tokens")
        print(f"  per type: " + ", ".join(f"{k} {v:+.0f}" for k, v in delta["per_problem_type_points"].items()))
    print("\nFull evidence: course/results/week7_ask_experiment.json")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arms", nargs="+", choices=list(ARMS), default=list(ARMS))
    args = parser.parse_args()
    asyncio.run(run(args.arms))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
