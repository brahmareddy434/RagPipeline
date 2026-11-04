"""Tests for the Task Set C machinery: handbook lookups, the assertion split, the blind
label seal, and the race scoring. All offline - no Ollama, no network."""
import json
from pathlib import Path

import pytest

from app import handbook
from app import week6_assertions as wa
from app.answer_quality import ABSTENTION, attribute
from course import race

ROOT = Path(__file__).resolve().parents[1]
WEEK6 = ROOT / "evaluation" / "week6"


# ------------------------------------------------------------------ handbook as data

def test_every_clause_number_is_unique_and_resolvable():
    clauses = handbook.clauses()
    assert len(clauses) > 30
    for number in clauses:
        assert handbook.clause_exists(number)


@pytest.mark.parametrize("number", ["2.1", "2.2", "2.3", "3.1", "4.6", "9.2", "9.3"])
def test_clauses_the_eval_set_depends_on_exist(number):
    assert handbook.clause_exists(number)


@pytest.mark.parametrize("number", ["2.99", "0.1", "12.4", ""])
def test_invented_clause_numbers_do_not_resolve(number):
    assert not handbook.clause_exists(number)


def test_jurisdiction_enum_comes_from_the_documents():
    assert handbook.jurisdictions() == ("IN", "UK", "DE", "US")
    for code in handbook.jurisdictions():
        assert handbook.annex(code) is not None
    assert handbook.annex("FR") is None


def test_version_detection_is_not_fooled_by_a_different_version():
    assert handbook.cites_version("based on Handbook v3.2")
    assert handbook.cites_version("handbook version 3.2 applies")
    assert not handbook.cites_version("based on Handbook v2.1")
    assert not handbook.cites_version("no version mentioned")


# ------------------------------------------------------------------ Python-derived attribution

def test_clause_and_version_are_read_from_the_chunk_not_invented():
    # Chunks are stored with Markdown stripped, so the clause marker is plain text.
    chunk = ("Acorn Labs Employee Handbook v3.2 Section 2: Leave. "
             "2.2 Planned leave notice, two years or more. Give at least 5 working days in advance. "
             "2.3 Planned leave notice, under two years. Give at least 10 working days in advance.")
    assert attribute(chunk, "at least 10 working days in advance") == ("2.3", "v3.2")
    assert attribute(chunk, "at least 5 working days in advance") == ("2.2", "v3.2")


def test_markdown_is_stripped_so_quotes_are_plain_prose():
    """A model quotes the sentence it can read; '**2.1 ...**' in the stored chunk breaks that."""
    from app.document_loader import DocumentLoader
    raw = b"# Heading\n\n**2.1 Annual leave allowance.** Employees receive 20 paid leave days per year.\n"
    text = DocumentLoader().load("s.md", raw)[0][1]
    assert "**" not in text and "#" not in text
    assert "2.1 Annual leave allowance. Employees receive 20 paid leave days per year." in text


def test_the_prompt_contains_no_sentence_that_could_be_copied_as_policy():
    """A worked example written as realistic policy gets quoted back as if it were context.

    Observed: the model returned 'Staff receive 12 annual leave days per year.' as an
    evidence quote. That sentence existed only in the prompt's addition example.
    """
    from app.prompts import PromptBuilder
    for prompt in (PromptBuilder.SYSTEM, PromptBuilder.COMPACT):
        assert "Staff receive" not in prompt
        for banned in ("annual leave days per year", "sick leave days per year"):
            assert banned not in prompt, f"{banned!r} reads as policy and will be copied into a quote"


def test_a_tool_result_gets_no_handbook_attribution():
    assert attribute("Asha Rao has 12 annual leave days remaining.", "12 annual") == ("", "")


# ------------------------------------------------------------------ the assertion / judge split

def test_four_criteria_were_moved_out_of_the_judge_leaving_one():
    counts = wa.split_counts()
    assert counts["assertions_moved_out_of_judge"] >= 2, "the task set requires at least 2"
    assert counts["assertions_moved_out_of_judge"] == 4
    assert counts["judged_criteria"] == 1


def test_the_moved_criteria_are_absent_from_the_judge_prompt():
    """Moving a criterion means deleting it from the prompt, not just adding a rule."""
    prompt = (WEEK6 / "judge_v1.txt").read_text(encoding="utf-8").casefold()
    for phrase in ("resolves to a real section", "handbook version is cited",
                   "notice period is written as a number", "out-of-jurisdiction question was refused"):
        assert phrase in prompt, "the prompt must name what it no longer grades"
    # And it must say it does not grade them.
    marker = prompt.index("do not grade")
    for phrase in ("section reference", "handbook version", "notice period", "out-of-jurisdiction"):
        assert prompt.index(phrase) > marker, f"{phrase} must appear under the DO NOT GRADE heading"


def test_judge_prompt_has_exactly_one_criterion_and_is_binary():
    prompt = (WEEK6 / "judge_v1.txt").read_text(encoding="utf-8")
    assert "THE SINGLE CRITERION" in prompt
    assert "Pass or fail" in prompt
    assert "1-10" not in prompt and "1 to 10" not in prompt


def case(**over):
    base = {"answerable": True, "question": "How many leave days?", "required_facts": [],
            "must_not_contain": []}
    base.update(over)
    return base


def test_section_assertion_needs_a_reference_that_resolves():
    good = "Employees receive 20 days. [1] (Handbook v3.2 Section 2.1)"
    assert wa.run_assertions(good, case(required_facts=["20"]))["checks"]["section_reference_resolves"]
    invented = "Employees receive 20 days. [1] (Handbook v3.2 Section 2.99)"
    assert not wa.run_assertions(invented, case())["checks"]["section_reference_resolves"]
    missing = "Employees receive 20 days. [1]"
    assert not wa.run_assertions(missing, case())["checks"]["section_reference_resolves"]


def test_version_assertion_catches_a_missing_version():
    assert not wa.run_assertions("Employees receive 20 days. [1] (Section 2.1)",
                                 case())["checks"]["handbook_version_cited"]


def test_notice_assertion_only_applies_to_notice_questions():
    notice = case(question="How much notice is needed for planned leave?")
    assert wa.run_assertions("Give at least 10 working days. [1] (Handbook v3.2 Section 2.3)",
                             notice)["checks"]["notice_figure_is_numeric"]
    assert not wa.run_assertions("Give plenty of notice. [1] (Handbook v3.2 Section 2.3)",
                                 notice)["checks"]["notice_figure_is_numeric"]
    other = case(question="Where do I report a suspicious email?")
    assert "notice_figure_is_numeric" in wa.run_assertions("security@acorn.example [1]", other)["skipped"]


def test_out_of_jurisdiction_must_refuse_not_borrow_the_nearest_annex():
    france = case(answerable=False, out_of_jurisdiction=True,
                  question="How many leave days does an employee in France receive?")
    assert wa.run_assertions(ABSTENTION, france)["checks"]["out_of_jurisdiction_refused"]
    borrowed = "An employee in France receives 28 days. [1] (Handbook v3.2 Section 9.2)"
    assert not wa.run_assertions(borrowed, france)["checks"]["out_of_jurisdiction_refused"]


def test_the_frozen_regressions_still_fail_the_assertions_they_were_saved_for():
    """A regression case is worthless if the current rules would let the old bug through."""
    cases = {c["id"]: c for c in json.loads((WEEK6 / "eval_set.json").read_text(encoding="utf-8"))["cases"]}
    leak = cases["reg_source_label_leak"]
    result = wa.run_assertions(leak["frozen_answer"], leak)
    assert not result["checks"]["no_internal_source_label"]
    assert not result["pass"]

    no_marker = cases["reg_missing_citation_marker"]
    result = wa.run_assertions(no_marker["frozen_answer"], no_marker)
    assert not result["checks"]["citation_marker_present"]
    assert not result["pass"]


def test_eval_set_meets_the_task_set_minimums():
    data = json.loads((WEEK6 / "eval_set.json").read_text(encoding="utf-8"))
    cases = data["cases"]
    assert len(cases) >= 25, "the task set requires 25+ cases"
    assert sum(c["kind"] == "regression" for c in cases) >= 2, "at least 2 verbatim regressions"
    modes = set(data["taxonomy_modes"])
    assert all(c["mode"] in modes for c in cases), "every case carries one Week-5 taxonomy mode"
    assert len({c["id"] for c in cases}) == len(cases)
    for c in cases:
        if c["expected_clause"]:
            assert handbook.clause_exists(c["expected_clause"])


# ------------------------------------------------------------------ the blind label seal

def test_seal_detects_an_edited_label_file(tmp_path, monkeypatch):
    import evaluation.week6.agreement as ag

    answers = {"answers_sha256": "abc", "answers": [{"id": "x", "question": "q", "answer": "a",
                                                     "mode": "citation_traceability"}]}
    labels = {"answers_sha256": "abc", "labels": [{"id": "x", "human_pass": True}]}
    (tmp_path / "answers.json").write_text(json.dumps(answers), encoding="utf-8")
    (tmp_path / "labels_25.json").write_text(json.dumps(labels), encoding="utf-8")
    receipt = {"labels_sha256": ag.sha256_of(labels["labels"]), "sealed_at": "2026-09-22T00:00:00Z"}
    (tmp_path / "labels_receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
    monkeypatch.setattr(ag, "ANSWERS", tmp_path / "answers.json")
    monkeypatch.setattr(ag, "LABELS", tmp_path / "labels_25.json")
    monkeypatch.setattr(ag, "RECEIPT", tmp_path / "labels_receipt.json")

    assert ag.verify_seal()["labelled"] == [{"id": "x", "human_pass": True}]

    # Flip a label after sealing: the run must refuse rather than report a number.
    labels["labels"][0]["human_pass"] = False
    (tmp_path / "labels_25.json").write_text(json.dumps(labels), encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        ag.verify_seal()
    assert "SEAL BROKEN" in str(exc.value)


def test_agreement_requires_both_classes_before_accepting_a_judge():
    import evaluation.week6.agreement as ag
    all_pass = [{"id": str(i), "human_pass": True, "judge_pass": True} for i in range(10)]
    result = ag.agreement(all_pass)
    assert result["agreement_percent"] == 100.0
    assert result["accepted"] is False, "100% on an all-pass set must not be accepted"

    mixed = ([{"id": "p", "human_pass": True, "judge_pass": True}] * 8
             + [{"id": "n", "human_pass": False, "judge_pass": False}] * 2)
    assert ag.agreement(mixed)["accepted"] is True


def test_agreement_separates_false_passes_from_false_fails():
    import evaluation.week6.agreement as ag
    rows = [{"id": "a", "human_pass": True, "judge_pass": False},
            {"id": "b", "human_pass": False, "judge_pass": True},
            {"id": "c", "human_pass": True, "judge_pass": True}]
    result = ag.agreement(rows)
    assert result["judge_failed_what_human_passed"] == ["a"]
    assert result["judge_passed_what_human_failed"] == ["b"]


# ------------------------------------------------------------------ the race

def test_race_questions_meet_the_task_set_minimums():
    questions = race.QUESTIONS
    assert len(questions) == 10, "the task set asks for 10 employee questions"
    branching = [q for q in questions if q["branching"]]
    assert len(branching) >= 3, "at least 3 must depend on what an earlier step found"
    assert len({q["id"] for q in questions}) == 10
    for q in branching:
        assert q["branch_on"], "a branching question must name the field it branches on"


def test_race_scoring_is_deterministic_and_checks_abstention_both_ways():
    answerable = {"expect_abstention": False, "required_facts": ["10"], "forbidden_facts": []}
    assert race.score(answerable, {"answer": "Give 10 working days. [1]", "abstained": False,
                                   "validation_issues": []})["pass"]
    assert not race.score(answerable, {"answer": ABSTENTION, "abstained": True,
                                       "validation_issues": []})["pass"]
    refuse = {"expect_abstention": True, "required_facts": [], "forbidden_facts": []}
    assert race.score(refuse, {"answer": ABSTENTION, "abstained": True, "validation_issues": []})["pass"]
    assert not race.score(refuse, {"answer": "The rate is 5%. [1]", "abstained": False,
                                   "validation_issues": []})["pass"]


def test_race_numbers_include_p50_and_cost_per_question():
    rows = [{"usage": {"latency_ms": 1000, "total_tokens": 100, "cost_usd": 0.001, "model_calls": 2},
             "score": {"pass": True}, "branching": True, "abstained": False},
            {"usage": {"latency_ms": 3000, "total_tokens": 300, "cost_usd": 0.003, "model_calls": 4},
             "score": {"pass": False}, "branching": False, "abstained": False},
            {"usage": {"latency_ms": 2000, "total_tokens": 200, "cost_usd": 0.002, "model_calls": 3},
             "score": {"pass": True}, "branching": True, "abstained": False}]
    stats = race.numbers(rows)
    assert stats["p50_latency_ms"] == 2000, "p50 is the median, not the mean"
    assert stats["total_tokens"] == 600, "tokens are summed over every lap"
    assert stats["cost_per_question_usd"] == pytest.approx(0.002)
    assert stats["pass_rate"] == pytest.approx(2 / 3, abs=1e-4)  # stored rounded to 4 dp
    assert stats["pass_rate_branching"] == 1.0
    assert stats["pass_rate_non_branching"] == 0.0
