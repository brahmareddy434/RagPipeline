import asyncio
from app.domain.ports import StructuredModel, Retriever
from pathlib import PurePosixPath
from app.rag.grounding import ABSTENTION, validate_grounded_answer
from app.schemas import AnswerResponse, GroundedAnswer, RetrievalOptions
from app.legacy.leave_totals import annual_leave_total


class RagService:
    def __init__(self, retriever: Retriever, ollama: StructuredModel, prompts, min_relevance,
                 evidence_keep_ratio: float = 0.0, max_context_chunks: int = 0):
        self.retriever, self.ollama, self.prompts, self.min_relevance = retriever, ollama, prompts, min_relevance
        # 0 disables either filter, so the A/B experiment can run both behaviours.
        self.evidence_keep_ratio, self.max_context_chunks = evidence_keep_ratio, max_context_chunks

    @staticmethod
    def relevance(result):
        """The comparable 0-1 relevance of a result, or 0 when only BM25 matched it.

        Keyword-only hits have no semantic score, and a raw BM25 score is not on the same
        scale as min_relevance, so it must never be compared against it.
        """
        return result.semantic_score or (result.score if 0 < result.score <= 1 else 0.0)

    def select_evidence(self, results):
        """Keep only chunks close to the best match, so the model reads evidence not the corpus.

        Retrieval always returns k chunks even when one is relevant. On this corpus the filler
        regularly included injection-example.txt: wasted prompt tokens, and the one document
        we least want in context. Ranking is by fusion score, so compare on relevance, and
        never return nothing when there was a best match.
        """
        cap = self.max_context_chunks or len(results)
        if not results or not self.evidence_keep_ratio:
            return results[:cap]
        best = max(self.relevance(r) for r in results)
        if best <= 0:  # keyword-only mode: BM25 rank is the only signal available
            return results[:cap]
        floor = best * self.evidence_keep_ratio
        kept = [r for r in results if self.relevance(r) >= floor] or [max(results, key=self.relevance)]
        return kept[:cap]

    async def answer(self, question, temperature, k, options=None):
        options = options or RetrievalOptions(k=k)
        results, inspection = await self.retriever.inspect(question, options)
        # A weak best match means the corpus does not cover the question. This used to be
        # checked for semantic mode only, so hybrid mode could never abstain on relevance.
        # Keyword-only results score 0 here and are exempt: BM25 matched a literal term.
        best = max((self.relevance(r) for r in results), default=0.0)
        if not results or (best > 0 and best < self.min_relevance):
            return AnswerResponse(answer=ABSTENTION, confidence="low", abstained=True, retrieved=results, inspection=inspection)
        selected = self.select_evidence(results)
        if len(selected) != len(results):
            inspection = {**inspection, "evidence_selected": len(selected), "evidence_retrieved": len(results),
                          "dropped_sources": [r.source for r in results if r not in selected]}
        results = selected
        total = annual_leave_total(question, results)
        if total is not None:
            checked = validate_grounded_answer(total, results, inspection)
            if not checked.abstained:
                checked.inspection["answer_method"] = "verified_policy_sum"
                return checked
        messages = self.prompts.rag_messages(question, results)
        output = await self.ollama.structured(messages, GroundedAnswer, temperature=temperature)
        response = validate_grounded_answer(output, results, inspection)
        if response.validation_issues:
            output = await self.ollama.structured(messages + [{"role": "user", "content":
                "Your evidence failed validation. Use exact quotes from CONTEXT, valid context_number, and no citation markers inside statement. For derived totals, use calculations with individually quoted operands instead of writing the total in a claim. If unsupported set answerable=false. Errors: " + "; ".join(response.validation_issues)}],
                GroundedAnswer, retries=0, temperature=0)
            response = validate_grounded_answer(output, results, inspection)
        return response
