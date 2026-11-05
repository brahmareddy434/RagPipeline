"""Deterministic assertions for the Week 6 task set.

These are the criteria that were **taken out of the LLM judge**. Paying a model to decide
whether "Section 2.3" resolves to a real clause, or whether the handbook version appears in
the text, is paying for something `if` and a lookup table do for free and never get wrong
on an off day. What is left for the judge afterwards is exactly one criterion that needs
reading comprehension.

Each assertion carries the criterion wording it replaced, so the split is auditable and the
counts (assertions vs judged criteria) can be printed rather than claimed.
"""
import re
from dataclasses import dataclass
from typing import Callable

from app.legacy import handbook
from app.rag.grounding import ABSTENTION

_SECTION = re.compile(r"(?:Section|section|§)\s*\d+\.\d+")
_NOTICE_FIGURE = re.compile(r"\b\d+(?:\.\d+)?\s*(?:working\s+)?days?\b", re.I)
_NOTICE_QUESTION = re.compile(r"\bnotice\b|\bin advance\b|\bhow (?:much|many).*(?:notice|advance)\b", re.I)


@dataclass(frozen=True)
class Assertion:
    """One criterion a computer can settle, with the judge wording it came from."""
    name: str
    replaced_judge_criterion: str
    applies: Callable[[dict], bool]
    check: Callable[[str, dict], bool]


def _answerable(case: dict) -> bool:
    return bool(case.get("answerable"))


def _section_reference_resolves(answer: str, case: dict) -> bool:
    """A section reference must be present AND name a clause that really exists."""
    numbers = handbook.cited_clauses(answer)
    return bool(numbers) and all(handbook.clause_exists(n) for n in numbers)


def _handbook_version_cited(answer: str, case: dict) -> bool:
    return handbook.cites_version(answer)


def _notice_figure_is_numeric(answer: str, case: dict) -> bool:
    return bool(_NOTICE_FIGURE.search(answer))


def _out_of_jurisdiction_refused(answer: str, case: dict) -> bool:
    return answer.strip() == ABSTENTION


def _correct_abstention(answer: str, case: dict) -> bool:
    refused = answer.strip() == ABSTENTION
    return refused if not case.get("answerable") else not refused


def _required_facts_present(answer: str, case: dict) -> bool:
    lowered = answer.casefold()
    return all(fact.casefold() in lowered for fact in case.get("required_facts", []))


def _forbidden_absent(answer: str, case: dict) -> bool:
    lowered = answer.casefold()
    return not any(bad.casefold() in lowered for bad in case.get("must_not_contain", []))


def _no_internal_label(answer: str, case: dict) -> bool:
    return "SOURCE=" not in answer


def _citation_marker_present(answer: str, case: dict) -> bool:
    return bool(re.search(r"\[\d+\]", answer))


# The four criteria named by the task set, moved here out of the judge prompt.
MOVED_FROM_JUDGE: tuple[Assertion, ...] = (
    Assertion(
        name="section_reference_resolves",
        replaced_judge_criterion="Does the answer cite a handbook section, and is that section real?",
        applies=_answerable,
        check=_section_reference_resolves,
    ),
    Assertion(
        name="handbook_version_cited",
        replaced_judge_criterion="Does the answer state which handbook version it is based on?",
        applies=_answerable,
        check=_handbook_version_cited,
    ),
    Assertion(
        name="notice_figure_is_numeric",
        replaced_judge_criterion="For a notice-period question, is the notice given as a number of days?",
        applies=lambda case: _answerable(case) and bool(_NOTICE_QUESTION.search(case["question"])),
        check=_notice_figure_is_numeric,
    ),
    Assertion(
        name="out_of_jurisdiction_refused",
        replaced_judge_criterion="For a jurisdiction with no annex, did the answer refuse instead of using the nearest one?",
        applies=lambda case: bool(case.get("out_of_jurisdiction")),
        check=_out_of_jurisdiction_refused,
    ),
)

# Deterministic checks that were already rules before this week. Listed separately so the
# "moved out of the judge" claim counts only what actually moved.
ALREADY_DETERMINISTIC: tuple[Assertion, ...] = (
    Assertion("correct_abstention", "n/a - already a rule", lambda case: True, _correct_abstention),
    Assertion("required_facts_present", "n/a - already a rule", _answerable, _required_facts_present),
    Assertion("forbidden_text_absent", "n/a - already a rule", lambda case: True, _forbidden_absent),
    Assertion("no_internal_source_label", "n/a - already a rule", lambda case: True, _no_internal_label),
    Assertion("citation_marker_present", "n/a - already a rule", _answerable, _citation_marker_present),
)

ALL: tuple[Assertion, ...] = MOVED_FROM_JUDGE + ALREADY_DETERMINISTIC

# What the judge is left with after the split. One criterion, binary, needs comprehension.
JUDGED_CRITERIA: tuple[str, ...] = (
    "Does the answer correctly and completely answer the question using only the handbook?",
)


def run_assertions(answer: str, case: dict) -> dict:
    """Score one answer. Only applicable assertions count toward the pass."""
    results, skipped = {}, []
    for assertion in ALL:
        if assertion.applies(case):
            results[assertion.name] = bool(assertion.check(answer, case))
        else:
            skipped.append(assertion.name)
    return {
        "checks": results,
        "skipped": skipped,
        "pass": all(results.values()) if results else True,
    }


def split_counts() -> dict:
    """The numbers the task set asks to be reported, derived not typed."""
    return {
        "assertions_total": len(ALL),
        "assertions_moved_out_of_judge": len(MOVED_FROM_JUDGE),
        "assertions_already_deterministic": len(ALREADY_DETERMINISTIC),
        "judged_criteria": len(JUDGED_CRITERIA),
        "moved_criteria": [a.replaced_judge_criterion for a in MOVED_FROM_JUDGE],
        "remaining_judged_criteria": list(JUDGED_CRITERIA),
    }
