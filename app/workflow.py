"""Week 7: the identical task as a fixed workflow. Same tools, same model, same contract.

There is no loop and no model decision about what happens next. The stages are hard-coded,
and they run in this order every single time:

    1. regex-extract an employee id; if present, get_employee_record        (0 model calls)
    2. if that record named a jurisdiction, get_jurisdiction_rules for it   (0 model calls)
    3. one hybrid search_handbook on the question exactly as it was asked   (0 model calls)
    4. one grounded generation over whatever stages 1-3 produced            (1 model call)

Stage 2 reads a field out of stage 1's output, which is ordinary data flow between fixed
steps, not the model choosing a path. The distinction that matters for the Week 7 verdict:
this pipeline always performs the same four stages in the same order, so its cost and
latency are predictable, while an agent's are not.

Its structural limit is stage 3. The search text is the user's question, so the workflow
can never search for a term it only *learned* in stage 1 or 2 - a project code with its own
deadline, or a clause that only applies under two years of service. Where the right search
depends on the record, the agent's extra laps are the thing being paid for. Whether that
case actually occurs in your traffic is what the race measures.
"""
import re
import time

from app.agent_tools import ToolFailure
from app.answer_quality import ABSTENTION, validate_grounded_answer
from app.models import AnswerResponse, GroundedAnswer, RetrievalOptions, WorkflowRunResponse, usd_cost
from app.ollama_client import call_metrics

EMPLOYEE_ID = re.compile(r"\bEMP-\d{4}\b", re.IGNORECASE)
JURISDICTION = re.compile(r"jurisdiction ([A-Z]{2})")

FINAL = """Answer the employee's HR question using only the CONTEXT.
Context items come from the Acorn Labs handbook and, when the question named an employee id,
that employee's record and their jurisdiction annex. Follow the schema exactly."""


class FixedWorkflow:
    """Deterministic pipeline: record -> jurisdiction -> handbook -> answer. No loop."""

    def __init__(self, retriever, ollama, prompts, registry, k: int = 6):
        self.retriever, self.ollama, self.prompts, self.registry, self.k = retriever, ollama, prompts, registry, k

    async def run(self, task: str) -> WorkflowRunResponse:
        started = time.perf_counter()
        outer = call_metrics.get()
        metrics: list[dict] = []
        token = call_metrics.set(metrics)
        steps, evidence = [], []
        try:
            # Stage 1 - fixed record lookup. No model involved in the decision.
            record_text = ""
            match = EMPLOYEE_ID.search(task)
            if match:
                try:
                    observation = self.registry.get_employee_record(match.group(0))
                    record_text = observation.text
                    evidence.extend(observation.evidence)
                    steps.append({"stage": "get_employee_record", "input": match.group(0),
                                  "output": observation.text, "ok": True})
                except ToolFailure as exc:
                    steps.append({"stage": "get_employee_record", "input": match.group(0),
                                  "output": str(exc), "ok": False})
            else:
                steps.append({"stage": "get_employee_record", "input": None,
                              "output": "No employee id in the question; skipped.", "ok": True})

            # Stage 2 - fixed jurisdiction lookup, keyed off stage 1's output. Still no model.
            found = JURISDICTION.search(record_text)
            if found:
                try:
                    observation = self.registry.get_jurisdiction_rules(found.group(1))
                    evidence.extend(observation.evidence)
                    steps.append({"stage": "get_jurisdiction_rules", "input": found.group(1),
                                  "output": observation.text, "ok": True})
                except ToolFailure as exc:
                    steps.append({"stage": "get_jurisdiction_rules", "input": found.group(1),
                                  "output": str(exc), "ok": False})
            else:
                steps.append({"stage": "get_jurisdiction_rules", "input": None,
                              "output": "No jurisdiction on the record; skipped.", "ok": True})

            # Stage 3 - one handbook search, on the question exactly as it was asked.
            results = await self.retriever.search(task, self.k, RetrievalOptions(k=self.k, mode="hybrid"))
            evidence.extend(results)
            steps.append({"stage": "search_handbook", "input": task,
                          "output": (f"{len(results)} clauses from "
                                     + ", ".join(sorted({r.source for r in results}))) if results
                                    else "No handbook clause matched.", "ok": bool(results)})

            # Stage 4 - one grounded generation.
            answer = await self._answer(task, evidence)
            steps.append({"stage": "generate_answer", "input": f"{len(evidence)} context items",
                          "output": answer.answer, "ok": not answer.abstained})
            prompt_tokens = sum(m.get("prompt_eval_count") or 0 for m in metrics)
            completion_tokens = sum(m.get("eval_count") or 0 for m in metrics)
            return WorkflowRunResponse(
                task=task, answer=answer.answer, citations=answer.citations, confidence=answer.confidence,
                abstained=answer.abstained, validation_issues=answer.validation_issues,
                evidence=answer.retrieved, steps=steps,
                usage={"steps": len(steps), "model_calls": len(metrics),
                       "prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens,
                       "total_tokens": prompt_tokens + completion_tokens,
                       "cost_usd": usd_cost(prompt_tokens, completion_tokens),
                       "latency_ms": round((time.perf_counter() - started) * 1000, 2)})
        finally:
            call_metrics.reset(token)
            if outer is not None:
                outer.extend(metrics)

    async def _answer(self, task: str, evidence: list) -> AnswerResponse:
        unique, seen = [], set()
        for item in evidence:
            if item.id not in seen:
                seen.add(item.id)
                unique.append(item.model_copy(update={"rank": len(unique) + 1}))
        if not unique:
            return AnswerResponse(answer=ABSTENTION, confidence="low", abstained=True, retrieved=[])
        messages = self.prompts.rag_messages(task, unique)
        messages[0]["content"] = FINAL + "\n\n" + messages[0]["content"]
        output = await self.ollama.structured(messages, GroundedAnswer, temperature=0)
        response = validate_grounded_answer(output, unique, {"question": task, "evidence_items": len(unique)})
        if response.validation_issues:
            output = await self.ollama.structured(messages + [{"role": "user", "content":
                "Your evidence failed validation. Quote exactly from CONTEXT, use a valid context_number, and "
                "put no citation markers inside statement. If unsupported set answerable=false. Errors: "
                + "; ".join(response.validation_issues)}], GroundedAnswer, retries=0, temperature=0)
            response = validate_grounded_answer(output, unique, response.inspection)
        return response
