from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class RetrievalOptions(StrictModel):
    mode: Literal["semantic", "keyword", "hybrid"] = "hybrid"
    k: int = Field(4, ge=1, le=20)
    source: str | None = Field(None, max_length=255)
    rerank: Literal["none", "mmr", "cross_encoder"] = "none"
    query_transform: Literal["none", "rewrite", "hyde"] = "none"

    @model_validator(mode="after")
    def normalize_optional_source(self):
        # FastAPI/Swagger uses "string" as the example for optional strings.
        # Treat that placeholder, and whitespace-only input, as no filename filter.
        if self.source is not None and self.source.strip().casefold() in {"", "string"}:
            self.source = None
        return self


class Chunk(BaseModel):
    id: str
    text: str
    source: str
    page: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchResult(Chunk):
    score: float = Field(ge=0)
    rank: int = Field(ge=1)
    retrieval_method: str
    semantic_score: float = 0.0
    keyword_score: float = 0.0
    fusion_score: float = 0.0
    rerank_score: float | None = None


class ChatRequest(StrictModel):
    question: str = Field(min_length=2, max_length=2000)
    temperature: float = Field(0.1, ge=0, le=2)
    retrieval: RetrievalOptions = Field(default_factory=RetrievalOptions)


class Citation(BaseModel):
    source: str
    page: int | None = None
    chunk_id: str
    number: int = Field(1, ge=1)
    url: str = ""
    quote: str = ""
    # Derived by Python from the cited chunk, never asked of the model: the handbook clause
    # the quote sits in, and the handbook version it came from. A lookup cannot hallucinate.
    clause: str = ""
    handbook_version: str = ""


class EvidenceClaim(StrictModel):
    statement: str = Field(min_length=1, max_length=1500)
    context_number: int = Field(ge=1)
    quote: str = Field(min_length=1, max_length=4000)


class CalculationOperand(StrictModel):
    value: float = Field(ge=0, le=1_000_000_000, allow_inf_nan=False)
    context_number: int = Field(ge=1)
    quote: str = Field(min_length=12, max_length=4000)


class EvidenceSum(StrictModel):
    label: str = Field(min_length=1, max_length=150)
    unit: str = Field(min_length=1, max_length=60)
    operands: list[CalculationOperand] = Field(min_length=2, max_length=12)


class GroundedAnswer(StrictModel):
    answerable: bool
    claims: list[EvidenceClaim] = Field(default_factory=list, max_length=12)
    calculations: list[EvidenceSum] = Field(default_factory=list, max_length=3)

    @model_validator(mode="after")
    def consistent_answerability(self):
        if self.answerable != bool(self.claims or self.calculations):
            raise ValueError("answerable=true requires claims or calculations; answerable=false requires both lists empty")
        return self


class AnswerResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    confidence: Literal["low", "medium", "high"]
    retrieved: list[SearchResult] = Field(default_factory=list)
    abstained: bool = False
    validation_issues: list[str] = Field(default_factory=list)
    inspection: dict[str, Any] = Field(default_factory=dict)


class ToolRequest(StrictModel):
    question: str = Field(min_length=2, max_length=1000)


class ToolDecision(BaseModel):
    tool: Literal["calculator", "order_lookup", "none"]
    arguments: dict[str, Any] = Field(default_factory=dict)
    direct_answer: str | None = None


class CalculatorArguments(StrictModel):
    expression: str = Field(min_length=1, max_length=200)


class OrderArguments(StrictModel):
    order_id: str = Field(pattern=r"^ORD-\d{4}$")


class ParallelToolRequest(StrictModel):
    questions: list[ToolRequest] = Field(min_length=1, max_length=4)


class InspectRequest(StrictModel):
    question: str = Field(min_length=2, max_length=2000)
    retrieval: RetrievalOptions = Field(default_factory=RetrievalOptions)


class EvaluationCase(StrictModel):
    question: str = Field(min_length=2, max_length=2000)
    expected_source: str = Field(min_length=1)
    relevant_sources: list[str] = Field(default_factory=list)


class EvaluationRequest(BaseModel):
    cases: list[EvaluationCase] = Field(min_length=1, max_length=100)
    k: int = Field(3, ge=1, le=20)
    mode: Literal["semantic", "keyword", "hybrid"] = "hybrid"


class EvaluationResponse(BaseModel):
    hit_rate_at_k: float
    mrr: float
    recall_at_k: float = 0.0
    cases: list[dict[str, Any]]


class IngestResponse(BaseModel):
    files: int
    chunks: int


class ChunkingOptions(BaseModel):
    chunk_size: int = Field(900, ge=200, le=4000)
    overlap: int = Field(150, ge=0, le=1000)

    @model_validator(mode="after")
    def overlap_must_be_smaller(self):
        if self.overlap >= self.chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")
        return self


# ---------------------------------------------------------------- Week 7: agents


# Assumed reference price used to turn token counts into a cost per question. Local Ollama
# inference is free, so this is a MODELLED cost for the agent-versus-workflow comparison,
# not a bill anyone paid. Only the ratio between the two systems is meaningful.
PROMPT_USD_PER_MTOK = 0.20
COMPLETION_USD_PER_MTOK = 0.60


def usd_cost(prompt_tokens: int, completion_tokens: int) -> float:
    """Modelled cost of one run at the reference rate above."""
    return round(prompt_tokens / 1e6 * PROMPT_USD_PER_MTOK
                 + completion_tokens / 1e6 * COMPLETION_USD_PER_MTOK, 8)


class AgentBudget(StrictModel):
    """Every ceiling that can stop a run. Defaults are sized for a 3-4B local model.

    The four the Week 7 task set requires are max_steps (iterations), max_tokens, max_cost
    and max_seconds (wall clock). Each one is checked inside the loop on every lap, not
    declared and forgotten. max_tool_errors and max_repeats are extra guards.

    max_steps default: a trajectory eval over course/week8_questions.json showed this model
    rarely chooses `finish` on its own - it rides whatever ceiling is set, padding out the
    remaining laps with tools the question does not need (a jurisdiction lookup called five
    times on a question naming no employee; `calculate` called on a question with no
    arithmetic). None of the ten questions need more than 3 real tool calls. Capping the
    ceiling near that, instead of far above it, bounds the waste directly rather than hoping
    a prompt instruction ("STOP EARLY") gets followed.
    """
    max_steps: int = Field(4, ge=1, le=20)
    max_seconds: float = Field(180.0, gt=0, le=900)
    max_tokens: int = Field(16000, ge=500, le=200_000)
    max_cost_usd: float = Field(0.02, gt=0, le=100)
    max_tool_errors: int = Field(3, ge=1, le=10)
    max_repeats: int = Field(2, ge=1, le=10)
    scratchpad_chars: int = Field(6000, ge=500, le=60_000)


class AgentRequest(StrictModel):
    task: str = Field(min_length=2, max_length=2000)
    session_id: str | None = Field(None, max_length=64, pattern=r"^[A-Za-z0-9_.:-]+$")
    budget: AgentBudget = Field(default_factory=AgentBudget)


class WorkflowRequest(StrictModel):
    task: str = Field(min_length=2, max_length=2000)


class AgentRunResponse(BaseModel):
    task: str
    session_id: str | None = None
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    confidence: Literal["low", "medium", "high"] = "low"
    abstained: bool = False
    validation_issues: list[str] = Field(default_factory=list)
    evidence: list[SearchResult] = Field(default_factory=list)
    steps: list[dict[str, Any]] = Field(default_factory=list)
    stop_reason: str
    stop_detail: str = ""
    completed: bool = False
    recalled_memory: list[str] = Field(default_factory=list)
    memory_summarisations: int = 0
    scratchpad_summary: str = ""
    budget: AgentBudget = Field(default_factory=AgentBudget)
    usage: dict[str, Any] = Field(default_factory=dict)


class WorkflowRunResponse(BaseModel):
    task: str
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    confidence: Literal["low", "medium", "high"] = "low"
    abstained: bool = False
    validation_issues: list[str] = Field(default_factory=list)
    evidence: list[SearchResult] = Field(default_factory=list)
    steps: list[dict[str, Any]] = Field(default_factory=list)
    usage: dict[str, Any] = Field(default_factory=dict)


class MemoryRequest(StrictModel):
    session_id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_.:-]+$")
    facts: list[str] = Field(default_factory=list, max_length=20)
