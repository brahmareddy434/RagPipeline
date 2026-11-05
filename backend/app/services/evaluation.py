import asyncio
from pathlib import PurePosixPath
from app.rag.grounding import ABSTENTION, validate_grounded_answer
from app.schemas import AnswerResponse, GroundedAnswer, RetrievalOptions
from app.legacy.leave_totals import annual_leave_total


class EvaluationService:
    def __init__(self, retriever):
        self.retriever = retriever

    async def evaluate(self, cases, k, mode="hybrid"):
        rows, hits, reciprocal_sum, recall_sum = [], 0, 0., 0.
        for case in cases:
            results = await self.retriever.search(case.question, k, RetrievalOptions(k=k, mode=mode))
            relevant = set(case.relevant_sources or [case.expected_source])
            rank = next((r.rank for r in results if r.source in relevant), None)
            recall = len({r.source for r in results} & relevant) / len(relevant)
            hits += int(rank is not None)
            reciprocal_sum += 1 / rank if rank else 0
            recall_sum += recall
            rows.append({"question": case.question, "expected_source": case.expected_source, "found_rank": rank,
                         "recall_at_k": recall, "retrieved_sources": [r.source for r in results]})
        return hits / len(cases), reciprocal_sum / len(cases), recall_sum / len(cases), rows
