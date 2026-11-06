"""Week 7 tests. All offline: a scripted fake model stands in for Ollama, so the loop's
control flow, budgets and safety properties are tested without a live service."""
import asyncio

import pytest

from app.agents.loop import PolicyAgent, decision_schema
from app.agents.tools import Observation, ToolFailure, ToolRegistry, as_evidence
from app.rag.grounding import ABSTENTION
from app.agents.memory import AgentStepRecord, Scratchpad, VectorMemory
from app.schemas import AgentBudget, GroundedAnswer, SearchResult
from app.rag.prompts import PromptBuilder
from app.services.tools import Calculator
from app.repositories.vector_store import VectorStore
from app.agents.workflow import FixedWorkflow

EMPLOYEES = {"EMP-1001": {"employee_id": "EMP-1001", "name": "Asha Rao", "reporting_manager": "Devan Pillai",
                          "project_code": "ORCHID-77", "jurisdiction": "IN", "hire_date": "2022-03-14",
                          "tenure_years": 4.5, "annual_leave_balance_days": 12,
                          "sick_leave_taken_days": 3, "carried_forward_days": 4}}


class FakeRetriever:
    """Returns one fixed passage so tool behaviour, not retrieval quality, is under test."""
    def __init__(self, text="Employees receive 20 paid leave days per year.", source="leave-policy.txt"):
        self.text, self.source, self.queries = text, source, []

    async def search(self, query, k, options=None):
        self.queries.append(query)
        if not self.text:
            return []
        return [SearchResult(id="c1", text=self.text, source=self.source, score=0.9, semantic_score=0.9,
                             rank=1, retrieval_method="hybrid_rrf")]


class FakeOllama:
    """Replays a script of decisions, then a final GroundedAnswer."""
    chat_model, embed_model = "fake-chat", "fake-embed"

    def __init__(self, decisions, final=None, chat_reply="compressed notes"):
        self.decisions, self.final, self.chat_reply = list(decisions), final, chat_reply
        self.structured_calls, self.chat_calls = 0, 0

    async def structured(self, messages, schema, retries=2, temperature=0):
        self.structured_calls += 1
        if schema is GroundedAnswer:
            return self.final or GroundedAnswer(answerable=False)
        if not self.decisions:
            return schema(thought="out of script", tool="finish", arguments={"summary": "done"})
        return schema.model_validate(self.decisions.pop(0))

    async def chat(self, messages, temperature=0.1, **options):
        self.chat_calls += 1
        return self.chat_reply

    async def embed(self, texts):
        return [[1.0, float(len(t) % 7 + 1), 0.5] for t in texts]


def registry(retriever=None):
    return ToolRegistry(retriever or FakeRetriever(), Calculator(), EMPLOYEES)


def agent(ollama, retriever=None, memory=None):
    return PolicyAgent(ollama, registry(retriever), PromptBuilder(), memory)


# ------------------------------------------------------------------ tool layer

def test_tool_catalogue_names_every_tool_and_its_arguments():
    catalogue = registry().catalogue()
    for name in ("search_handbook", "get_employee_record", "get_jurisdiction_rules",
                 "calculate", "finish"):
        assert name in catalogue
    assert "employee_id" in catalogue and "expression" in catalogue
    # The enum values must reach the model, not just the schema.
    assert "jurisdiction=IN|UK|DE|US" in catalogue


def test_decision_schema_rejects_an_invented_tool():
    schema = decision_schema(registry().names)
    with pytest.raises(Exception):
        schema.model_validate({"thought": "t", "tool": "delete_everything", "arguments": {}})


@pytest.mark.parametrize("name,arguments", [
    ("get_employee_record", {"employee_id": "1001"}),
    ("get_employee_record", {"employee_id": "EMP-99"}),
    ("get_jurisdiction_rules", {"jurisdiction": "FR"}),   # not in the enum
    ("get_jurisdiction_rules", {"jurisdiction": "uk"}),   # enum is case sensitive
    ("get_jurisdiction_rules", {}),                       # required argument missing
    ("calculate", {"expression": ""}),
    ("search_handbook", {"query": "a"}),
    ("unknown_tool", {}),
])
def test_python_rejects_bad_tool_arguments(name, arguments):
    with pytest.raises(ToolFailure):
        registry().validate(name, arguments)


async def test_unknown_employee_is_a_recoverable_tool_failure():
    with pytest.raises(ToolFailure):
        await registry().execute("get_employee_record", {"employee_id": "EMP-9999"})


async def test_tool_results_are_citable_evidence():
    observation = await registry().execute("get_employee_record", {"employee_id": "emp-1001"})
    assert observation.evidence[0].source == "tool:get_employee_record:EMP-1001"
    assert "ORCHID-77" in observation.evidence[0].text
    # The numeric-claim check in answer_quality needs the figure inside the quotable text.
    assert "12 annual leave days" in observation.evidence[0].text
    # Tenure and jurisdiction are the fields that make the path branch, so they must be
    # quotable too, or the agent cannot cite the reason it picked a clause.
    assert "4.5 completed years of service" in observation.evidence[0].text
    assert "jurisdiction IN" in observation.evidence[0].text


async def test_calculator_tool_still_refuses_unsafe_input():
    with pytest.raises(ValueError):
        await registry().execute("calculate", {"expression": "__import__('os')"})


# ------------------------------------------------------------------ the loop stops

async def test_loop_stops_at_the_step_ceiling_and_still_answers():
    """A model that never chooses finish must not run forever."""
    forever = [{"thought": "keep going", "tool": "search_handbook", "arguments": {"query": f"topic {i}"}}
               for i in range(50)]
    run = await agent(FakeOllama(forever)).run("anything", budget=AgentBudget(max_steps=3))
    assert run.stop_reason == "max_steps" and len(run.steps) == 3 and run.completed is False
    assert run.answer  # a bounded stop still produces an answer, not an exception


async def test_repeated_identical_calls_are_cached_then_stopped():
    same = [{"thought": "again", "tool": "search_handbook", "arguments": {"query": "leave"}} for _ in range(10)]
    retriever = FakeRetriever()
    run = await agent(FakeOllama(same), retriever).run("q", budget=AgentBudget(max_steps=8, max_repeats=2))
    assert run.stop_reason == "repeated_call"
    assert len(retriever.queries) == 1, "an identical call must be served from cache, not re-run"
    assert "already ran this exact call" in run.steps[1]["observation"]


async def test_repeated_tool_failures_stop_the_run():
    bad = [{"thought": "bad id", "tool": "get_employee_record", "arguments": {"employee_id": f"EMP-90{i}0"}}
           for i in range(10)]
    run = await agent(FakeOllama(bad)).run("q", budget=AgentBudget(max_steps=9, max_tool_errors=2))
    assert run.stop_reason == "tool_errors"
    assert all(step["ok"] is False for step in run.steps)


async def test_wall_clock_budget_stops_the_run():
    class SlowRetriever(FakeRetriever):
        async def search(self, query, k, options=None):
            await asyncio.sleep(0.05)
            return await super().search(query, k, options)

    script = [{"thought": "slow", "tool": "search_handbook", "arguments": {"query": f"q{i}"}} for i in range(50)]
    run = await agent(FakeOllama(script), SlowRetriever()).run("q", budget=AgentBudget(max_steps=20, max_seconds=0.12))
    assert run.stop_reason == "timeout" and len(run.steps) < 20


async def test_a_model_that_cannot_choose_a_tool_stops_instead_of_spinning():
    class Broken(FakeOllama):
        async def structured(self, messages, schema, retries=2, temperature=0):
            if schema is GroundedAnswer:
                return GroundedAnswer(answerable=False)
            raise RuntimeError("model offline")

    run = await agent(Broken([])).run("q")
    assert run.stop_reason == "model_error" and run.abstained


async def test_finish_ends_the_loop_immediately():
    script = [{"thought": "enough", "tool": "finish", "arguments": {"summary": "done"}}]
    run = await agent(FakeOllama(script)).run("q")
    assert run.stop_reason == "finished" and run.completed and run.steps == []


# ------------------------------------------------------------------ grounding

async def test_agent_abstains_when_no_tool_returned_evidence():
    empty = FakeRetriever(text="")
    script = [{"thought": "look", "tool": "search_handbook", "arguments": {"query": "dental premium"}},
              {"thought": "nothing", "tool": "finish", "arguments": {"summary": "not covered"}}]
    run = await agent(FakeOllama(script), empty).run("What is the dental premium?")
    assert run.abstained and run.answer == ABSTENTION and run.citations == []


async def test_agent_answer_is_validated_against_the_evidence_it_gathered():
    script = [{"thought": "search", "tool": "search_handbook", "arguments": {"query": "leave"}},
              {"thought": "done", "tool": "finish", "arguments": {"summary": "20 days"}}]
    good = GroundedAnswer(answerable=True, claims=[{"statement": "Employees receive 20 paid leave days per year.",
                                                    "context_number": 1,
                                                    "quote": "Employees receive 20 paid leave days per year."}])
    run = await agent(FakeOllama(script, final=good)).run("How many leave days?")
    assert not run.abstained and run.citations[0].source == "leave-policy.txt"
    assert run.validation_issues == []


async def test_a_quote_the_evidence_does_not_contain_is_rejected():
    script = [{"thought": "search", "tool": "search_handbook", "arguments": {"query": "leave"}},
              {"thought": "done", "tool": "finish", "arguments": {"summary": "x"}}]
    invented = GroundedAnswer(answerable=True, claims=[{"statement": "Employees receive 99 leave days.",
                                                        "context_number": 1,
                                                        "quote": "Employees receive 99 leave days."}])
    run = await agent(FakeOllama(script, final=invented)).run("How many leave days?")
    assert run.abstained and run.validation_issues


# ------------------------------------------------------------------ memory

def test_scratchpad_renders_every_step_and_reports_budget():
    pad = Scratchpad(char_budget=200, keep_recent=1)
    for i in range(3):
        pad.add(AgentStepRecord(index=i + 1, thought="t" * 40, tool="search_handbook",
                                arguments={"query": "q"}, observation="o" * 200))
    assert "Step 1" in pad.render() and "Step 3" in pad.render()
    assert pad.over_budget()


async def test_scratchpad_compression_keeps_recent_steps_and_summarises_the_rest():
    pad = Scratchpad(char_budget=100, keep_recent=1)
    for i in range(4):
        pad.add(AgentStepRecord(index=i + 1, thought="t", tool="search_handbook",
                                arguments={}, observation="x" * 200))
    ollama = FakeOllama([], chat_reply="Found the 14 day ORCHID-77 deadline.")
    await pad.compress(ollama)
    assert len(pad.steps) == 1 and pad.summarisations == 1
    assert "14 day" in pad.summary and "Summary of earlier steps" in pad.render()


async def test_long_runs_compress_short_term_memory_automatically():
    script = [{"thought": "s", "tool": "search_handbook", "arguments": {"query": f"q{i}"}} for i in range(5)]
    retriever = FakeRetriever(text="policy text " * 200)
    ollama = FakeOllama(script)
    run = await agent(ollama, retriever).run("q", budget=AgentBudget(max_steps=5, scratchpad_chars=900))
    assert run.memory_summarisations >= 1 and ollama.chat_calls >= 1


async def test_compression_shrinks_the_prompt_but_never_the_audit_trail():
    """Compression trims what the model re-reads. Every step must still be reported."""
    script = [{"thought": "s", "tool": "search_handbook", "arguments": {"query": f"q{i}"}} for i in range(6)]
    retriever = FakeRetriever(text="policy text " * 200)
    run = await agent(FakeOllama(script), retriever).run("q", budget=AgentBudget(max_steps=6, scratchpad_chars=900))
    assert run.memory_summarisations >= 1
    assert len(run.steps) == 6 and [s["index"] for s in run.steps] == [1, 2, 3, 4, 5, 6]
    assert run.usage["steps"] == 6


async def test_vector_memory_is_isolated_per_session(tmp_path):
    store = VectorStore(str(tmp_path / "mem"), "memory_test", FakeOllama([]))
    memory = VectorMemory(store)
    await memory.remember("alice", ["Alice is on project ORCHID-77."])
    await memory.remember("bob", ["Bob is on project BIRCH-12."])
    assert await memory.recall("alice", "which project", 3) == ["Alice is on project ORCHID-77."]
    assert await memory.all_facts("bob") == ["Bob is on project BIRCH-12."]
    assert await memory.forget("alice") == 1
    assert await memory.all_facts("alice") == []


async def test_agent_recalls_memory_and_stores_durable_facts(tmp_path):
    store = VectorStore(str(tmp_path / "mem"), "memory_agent", FakeOllama([]))
    memory = VectorMemory(store)
    script = [{"thought": "who", "tool": "get_employee_record", "arguments": {"employee_id": "EMP-1001"}},
              {"thought": "done", "tool": "finish", "arguments": {"summary": "ok"}}]
    first = await agent(FakeOllama(script), memory=memory).run("About EMP-1001?", session_id="s1")
    assert first.recalled_memory == []
    assert any("ORCHID-77" in fact for fact in await memory.all_facts("s1"))

    second = await agent(FakeOllama([{"thought": "done", "tool": "finish", "arguments": {"summary": "ok"}}]),
                         memory=memory).run("About EMP-1001?", session_id="s1")
    assert second.recalled_memory, "a second run in the same session must see the stored record"


# ------------------------------------------------------------------ fixed workflow

async def test_workflow_runs_four_fixed_stages_in_order():
    # Evidence is gathered in stage order, so context 1 is the record, 2 is the jurisdiction
    # annex read out of that record, and 3 is the handbook clause.
    good = GroundedAnswer(answerable=True, claims=[{"statement": "Employees receive 20 paid leave days per year.",
                                                    "context_number": 3,
                                                    "quote": "Employees receive 20 paid leave days per year."}])
    ollama = FakeOllama([], final=good)
    workflow = FixedWorkflow(FakeRetriever(), ollama, PromptBuilder(), registry())
    run = await workflow.run("How many leave days does EMP-1001 get?")
    assert [s["stage"] for s in run.steps] == ["get_employee_record", "get_jurisdiction_rules",
                                               "search_handbook", "generate_answer"]
    assert ollama.structured_calls == 1, "the fixed sequence must make exactly one generation call"
    assert run.citations[0].source == "leave-policy.txt" and run.validation_issues == []


async def test_workflow_retries_once_when_the_evidence_check_fails():
    """The one-call claim holds only for valid output; a bad quote costs a second call."""
    wrong = GroundedAnswer(answerable=True, claims=[{"statement": "Employees receive 20 paid leave days per year.",
                                                     "context_number": 1,
                                                     "quote": "Employees receive 20 paid leave days per year."}])
    ollama = FakeOllama([], final=wrong)
    workflow = FixedWorkflow(FakeRetriever(), ollama, PromptBuilder(), registry())
    run = await workflow.run("How many leave days does EMP-1001 get?")
    assert ollama.structured_calls == 2 and run.abstained


async def test_workflow_skips_lookup_when_no_employee_id_is_present():
    workflow = FixedWorkflow(FakeRetriever(), FakeOllama([]), PromptBuilder(), registry())
    run = await workflow.run("How many days per week may I work remotely?")
    assert run.steps[0]["input"] is None and "skipped" in run.steps[0]["output"]


async def test_workflow_abstains_when_retrieval_finds_nothing():
    workflow = FixedWorkflow(FakeRetriever(text=""), FakeOllama([]), PromptBuilder(), registry())
    run = await workflow.run("What is the dental premium?")
    assert run.abstained and run.answer == ABSTENTION


async def test_workflow_searches_the_raw_question_only_once():
    """This is exactly the limitation the race is designed to expose."""
    retriever = FakeRetriever()
    workflow = FixedWorkflow(retriever, FakeOllama([]), PromptBuilder(), registry(retriever))
    await workflow.run("EMP-1001 bought a flight 20 days ago, can they claim it?")
    assert len(retriever.queries) == 1
    assert "ORCHID-77" not in retriever.queries[0], "the fixed sequence cannot search on what it learned in step 1"


# ------------------------------------------------------------------ the third tool

async def test_jurisdiction_tool_returns_the_annex_as_citable_evidence():
    observation = await registry().execute("get_jurisdiction_rules", {"jurisdiction": "UK"})
    assert observation.evidence[0].source == "tool:get_jurisdiction_rules:UK"
    assert "9.2" in observation.text and "28 days" in observation.text
    assert "v3.2" in observation.text, "the annex must carry the handbook version it came from"


@pytest.mark.parametrize("code", ["IN", "UK", "DE", "US"])
async def test_every_enum_value_resolves_to_a_real_annex(code):
    observation = await registry().execute("get_jurisdiction_rules", {"jurisdiction": code})
    assert observation.evidence and code in observation.evidence[0].source


def test_the_three_tools_do_not_overlap_in_what_they_claim_to_do():
    """The 10-mark criterion: one job each, no description overlap."""
    tools = registry().tools
    for name in ("search_handbook", "get_employee_record", "get_jurisdiction_rules"):
        assert "ONE JOB" in tools[name].description
    # Each one states what it does NOT cover, which is what stops tool thrash.
    assert "nothing about any individual" in tools["search_handbook"].description
    assert "no handbook text" in tools["get_employee_record"].description
    assert "no general rules" in tools["get_jurisdiction_rules"].description


def test_cost_budget_is_a_real_ceiling_not_a_constant():
    from app.schemas import AgentBudget, usd_cost
    budget = AgentBudget()
    assert budget.max_cost_usd > 0
    assert usd_cost(1_000_000, 0) == pytest.approx(0.20)
    assert usd_cost(0, 1_000_000) == pytest.approx(0.60)
    assert usd_cost(0, 0) == 0


async def test_cost_budget_stops_the_run():
    """A run that blows the cost ceiling must stop, not merely record the number."""
    class CostlyOllama(FakeOllama):
        async def structured(self, messages, schema, retries=2, temperature=0):
            from app.infrastructure.ollama import call_metrics
            metrics = call_metrics.get()
            if metrics is not None:
                metrics.append({"prompt_eval_count": 1000, "eval_count": 1000})
            return await super().structured(messages, schema, retries=retries, temperature=temperature)

    script = [{"thought": "go", "tool": "search_handbook", "arguments": {"query": f"q{i}"}} for i in range(9)]
    # Cost is the binding ceiling here: 4000 tokens is well inside max_tokens, but three
    # laps at $0.0008 each passes $0.001. This proves cost is checked, not just recorded.
    run = await agent(CostlyOllama(script)).run(
        "q", budget=AgentBudget(max_steps=8, max_tokens=16_000, max_cost_usd=0.001))
    assert run.stop_reason == "cost_budget"
    assert run.usage["cost_usd"] > 0.001
    assert run.usage["total_tokens"] < 16_000, "the token ceiling must not be what fired"
