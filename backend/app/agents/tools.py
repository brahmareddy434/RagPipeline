"""Week 7 tool layer: three domain tools plus the loop's terminator.

Two rules carried over from Week 2 and never relaxed:

1. The model only ever *chooses* a tool name and arguments. Python validates those
   arguments against a Pydantic schema and Python executes the action.
2. Whatever a tool returns is untrusted data, never instructions.

Every tool also returns citable `evidence`. Structured tool output (an HR record, a
jurisdiction annex, an arithmetic result) is wrapped as a pseudo-chunk with a `tool:`
source so the final answer can quote it and pass the same Week 3-6 grounding validator as
a handbook chunk. Without that the agent could state a tenure or a balance it could not cite.

**Tool descriptions are the interface.** Each one names exactly one job and says what it
cannot do, so the three do not compete for the same question. The rule applied here:

    search_handbook      -> rules that apply to everybody (the written handbook)
    get_employee_record  -> facts about one named person
    get_jurisdiction_rules -> the country annex that overrides a general rule

`evaluation/week7/tool_descriptions_before.json` holds the previous wording and
`docs/DEMO_Week7_Agents.md` shows the diff. The old `search_policy` claimed to cover
"project addenda" while the old `lookup_employee` returned a "work location", so a
jurisdiction question matched both descriptions and tool choice was a coin toss.
"""
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, ValidationError

from app.legacy import handbook
from app.schemas import RetrievalOptions, SearchResult, StrictModel

from app.config.paths import PROJECT_ROOT as ROOT
EMPLOYEE_FILE = ROOT / "course" / "data" / "employees.json"

# A free-text HR field (a manager's comment) is written by a person, not by policy, and an
# attacker who can edit that field gets a free shot at the agent's context window - this is
# indirect prompt injection, the same class as a hostile web page or PDF. The record tool
# must return the *fact* that a comment exists without becoming a delivery channel for
# instructions hiding inside it. This is a keyword filter, not a semantic one: it catches the
# imperative phrasing this kind of attack actually uses, and it fails safe by dropping the
# whole sentence rather than trying to edit around it.
INJECTION_MARKERS = re.compile(
    r"ignore (all|any|previous|prior)|system override|do not mention|"
    r"auto[- ]?approv|without checking|reveal (hidden|your|the) prompt|act as|"
    r"disregard (all|any|previous|prior)",
    re.IGNORECASE,
)


def sanitize_free_text(text: str) -> str:
    """Drop any sentence in a free-text field that reads as an instruction, not a fact."""
    if not text:
        return text
    sentences = re.split(r"(?<=[.!?])\s+", text)
    kept = [s for s in sentences if not INJECTION_MARKERS.search(s)]
    if len(kept) == len(sentences):
        return text
    removed = len(sentences) - len(kept)
    rendered = " ".join(kept).strip()
    note = f"[{removed} sentence(s) removed: matched an embedded-instruction pattern]"
    return f"{rendered} {note}".strip()


class ToolFailure(ValueError):
    """A tool rejected its arguments or found nothing. Recoverable: the agent may retry."""


@dataclass
class Observation:
    """What one tool call produced: text the model reads, plus quotable evidence."""
    text: str
    evidence: list[SearchResult]


def as_evidence(source: str, text: str, chunk_id: str) -> SearchResult:
    """Wrap a tool result as a citable pseudo-chunk with the same shape as a retrieved one."""
    return SearchResult(id=chunk_id, text=text, source=source, page=None, metadata={"origin": "tool"},
                        score=1.0, rank=1, retrieval_method="tool")


class SearchHandbookArguments(StrictModel):
    query: str = Field(min_length=2, max_length=300)


class EmployeeArguments(StrictModel):
    employee_id: str = Field(pattern=r"^(?i:EMP)-\d{4}$")


class JurisdictionArguments(StrictModel):
    # The enum the task set asks for. Values come from the handbook's own annex headings,
    # so an unsupported country is rejected by the schema before any code runs.
    jurisdiction: Literal["IN", "UK", "DE", "US"]


class CalculateArguments(StrictModel):
    expression: str = Field(min_length=1, max_length=120)


class FinishArguments(StrictModel):
    summary: str = Field(min_length=2, max_length=600)


@dataclass(frozen=True)
class Tool:
    """One capability. `description` is prompt text, so it is written for the model."""
    name: str
    description: str
    arguments: type[BaseModel]
    terminal: bool = False


class ToolRegistry:
    """Holds the tools, renders the catalogue for the prompt, and dispatches safely."""

    def __init__(self, retriever, calculator, employees: dict[str, dict] | None = None, k: int = 4):
        self.retriever, self.calculator, self.k = retriever, calculator, k
        self.employees = employees if employees is not None else load_employees()
        self.tools: dict[str, Tool] = {t.name: t for t in (
            Tool(
                name="search_handbook",
                description=(
                    "Read the general Acorn Labs employee handbook and return the matching numbered "
                    "clauses. ONE JOB: the rule that applies to everybody. Use it for an allowance, "
                    "limit, deadline, notice period or process. Search one topic in a short phrase, "
                    "for example 'planned leave notice'. It knows nothing about any individual person "
                    "and nothing about country-specific overrides."
                ),
                arguments=SearchHandbookArguments,
            ),
            Tool(
                name="get_employee_record",
                description=(
                    "Return the HR record for ONE employee id such as EMP-1001. ONE JOB: facts about "
                    "that person only - name, reporting manager, project code, jurisdiction code, "
                    "completed years of service, leave balance, sick days taken, carry-forward days. "
                    "Call it first whenever a question names an employee, because their years of "
                    "service and jurisdiction decide which rule applies. It contains no handbook text "
                    "and no country rules."
                ),
                arguments=EmployeeArguments,
            ),
            Tool(
                name="get_jurisdiction_rules",
                description=(
                    "Return the handbook annex for ONE country code. ONE JOB: the country override "
                    "that replaces a general handbook rule. Allowed values are exactly IN, UK, DE, US "
                    "and nothing else. Call it after you know the employee's jurisdiction, and before "
                    "you state any allowance or notice period for them. It holds no general rules and "
                    "no personal data."
                ),
                arguments=JurisdictionArguments,
            ),
            Tool(
                name="calculate",
                description=(
                    "Evaluate ONE plain arithmetic expression built only from numbers and + - * / **, "
                    "for example '12 - 8'. Use it to subtract or compare days or balances instead of "
                    "doing the arithmetic yourself. It has no dates, units, words or functions: write "
                    "'30 - 20', never '30 days - 20 days' or 'date(today) + 30'."
                ),
                arguments=CalculateArguments,
            ),
            Tool(
                name="finish",
                description=(
                    "Stop and write the final answer. Choose this as soon as the gathered evidence can "
                    "answer the question, or as soon as it is clear the handbook does not cover it. "
                    "`summary` is a one-line statement of the conclusion."
                ),
                arguments=FinishArguments,
                terminal=True,
            ),
        )}

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(self.tools)

    def catalogue(self) -> str:
        """The tool list exactly as the model sees it, enum values included."""
        lines = []
        for tool in self.tools.values():
            schema = tool.arguments.model_json_schema()
            params = []
            for name, spec in schema.get("properties", {}).items():
                allowed = spec.get("enum")
                params.append(f"{name}" + (f"={'|'.join(allowed)}" if allowed else ""))
            lines.append(f"- {tool.name}({', '.join(params)}): {tool.description}")
        return "\n".join(lines)

    def validate(self, name: str, arguments: dict) -> BaseModel:
        tool = self.tools.get(name)
        if tool is None:
            raise ToolFailure(f"Unknown tool {name!r}. Choose one of: {', '.join(self.names)}.")
        try:
            return tool.arguments.model_validate(arguments or {})
        except ValidationError as exc:
            detail = "; ".join(f"{'.'.join(str(p) for p in e['loc']) or 'arguments'}: {e['msg']}"
                               for e in exc.errors(include_input=False))
            raise ToolFailure(f"Invalid arguments for {name}: {detail}") from exc

    async def execute(self, name: str, arguments: dict) -> Observation:
        """Validate then run. Only Python touches the data."""
        args = self.validate(name, arguments)
        if name == "search_handbook":
            return await self.search_handbook(args.query)
        if name == "get_employee_record":
            return self.get_employee_record(args.employee_id)
        if name == "get_jurisdiction_rules":
            return self.get_jurisdiction_rules(args.jurisdiction)
        if name == "calculate":
            return self.calculate(args.expression)
        raise ToolFailure(f"{name} is terminal and is handled by the agent loop, not executed as a tool.")

    async def search_handbook(self, query: str) -> Observation:
        results = await self.retriever.search(query, self.k, RetrievalOptions(k=self.k, mode="hybrid"))
        if not results:
            return Observation(f"No handbook clause matched {query!r}. Try different wording or another topic.", [])
        lines = [f"[{r.source}] {r.text}" for r in results]
        return Observation(f"{len(results)} handbook passages for {query!r}:\n" + "\n".join(lines), results)

    def get_employee_record(self, employee_id: str) -> Observation:
        record = self.employees.get(employee_id.upper())
        if record is None:
            raise ToolFailure(f"No HR record for {employee_id.upper()}. Known ids: {', '.join(sorted(self.employees))}.")
        # Rendered as sentences so the final answer can quote a fact verbatim and the
        # numeric-claim check in answer_quality.py can find each figure inside the quote.
        text = (
            f"{record['name']} ({record['employee_id']}) reports to {record['reporting_manager']} on project "
            f"{record['project_code']}. "
            f"{record['name']} has {record['tenure_years']} completed years of service. "
            f"{record['name']} works under jurisdiction {record['jurisdiction']}. "
            f"{record['name']} has {record['annual_leave_balance_days']} annual leave days remaining, "
            f"has taken {record['sick_leave_taken_days']} sick leave days this year, and has "
            f"{record['carried_forward_days']} carried-forward days."
        )
        if record.get("manager_comment"):
            text += (f" Manager note (free text, not policy, sanitized): "
                    f"{sanitize_free_text(record['manager_comment'])}")
        return Observation(text, [as_evidence(f"tool:get_employee_record:{record['employee_id']}", text,
                                              f"emp-{record['employee_id'].lower()}")])

    def get_jurisdiction_rules(self, jurisdiction: str) -> Observation:
        code = jurisdiction.strip().upper()
        clause = handbook.annex(code)
        if clause is None:
            raise ToolFailure(
                f"The handbook has no annex for {code}. Allowed jurisdictions are: "
                f"{', '.join(handbook.jurisdictions())}.")
        text = (f"Handbook {handbook.VERSION} Section {clause['number']} {clause['title']}: "
                f"{clause['text']}")
        return Observation(text, [as_evidence(f"tool:get_jurisdiction_rules:{code}", text,
                                              f"annex-{clause['number']}")])

    def calculate(self, expression: str) -> Observation:
        try:
            value = self.calculator.run(expression)
        except ValueError as exc:
            # A tool error is prompt text. Restating the contract and giving a worked example
            # is what lets the model recover; a bare "invalid expression" makes it retry the
            # same thing until the budget stops it. Observed with llama3.2:3b on date maths.
            raise ToolFailure(
                f"calculate could not evaluate {expression!r} ({exc}). It takes ONE plain arithmetic "
                "expression of numbers and + - * / ** only, for example '30 - 20'. It cannot do dates, "
                "units, words or function calls. Convert the quantities to numbers yourself and retry, "
                "or answer without it."
            ) from exc
        rendered = int(value) if float(value).is_integer() else round(value, 4)
        text = f"The expression {expression} equals {rendered}."
        return Observation(text, [as_evidence("tool:calculate", text,
                                              "calc-" + str(abs(hash((expression, rendered))))[:12])])


def load_employees(path: Path = EMPLOYEE_FILE) -> dict[str, dict]:
    return json.loads(path.read_text(encoding="utf-8"))["employees"]
