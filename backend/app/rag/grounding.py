import re
from decimal import Decimal
from app.legacy import handbook
from app.schemas import AnswerResponse, Citation, GroundedAnswer

ABSTENTION = "I don't know based on the uploaded documents."

def source_url(source):
    # Tool/resource evidence is embedded in the authorized run; it is not a Chroma ID.
    return "" if source.metadata.get("origin")=="tool" else f"/sources/{source.id}"
_CITATION = re.compile(r"\[(\d+)\]")

# Output guardrail, the last line of defense after tool-output sanitising (app.agents.tools.
# sanitize_free_text) and the per-claim source check below. It does not look at where a
# phrase came from, only whether the DRAFTED ANSWER itself states something no legitimate
# HR fact would ever contain - an unlimited/999-day balance, an auto-approval, a claim to
# have followed a hidden instruction. Any of these surviving into the answer means every
# earlier layer missed something, so this is deliberately generic rather than reusing the
# other layers' exact wording.
_INJECTION_ANSWER_MARKERS = ("unlimited", "999 day", "auto-approv", "auto approv",
                            "system override", "ignore previous instruction", "hidden instruction")


def flag_injected_language(answer: str) -> list[str]:
    lowered = answer.casefold()
    return [f"answer contains a known injection marker: {marker!r}" for marker in _INJECTION_ANSWER_MARKERS
            if marker in lowered]


def ensure_traceable_answer(answer: str, context_count: int) -> str:
    """Legacy free-text guard. Never fabricate a citation."""
    cleaned = re.sub(r"\s*SOURCE=[^,;:\n]+", "", answer).strip()
    if cleaned == ABSTENTION:
        return ABSTENTION
    refs = [int(n) for n in _CITATION.findall(cleaned)]
    if not refs or any(n < 1 or n > context_count for n in refs):
        return ABSTENTION
    return cleaned


def normalize(text):
    return " ".join(text.split()).casefold()


# A clause marker in a stored chunk, after Markdown stripping: a number at the start of a
# sentence followed by a capitalised title, e.g. "2.1 Annual leave allowance. Employees ...".
_CLAUSE_IN_CHUNK = re.compile(r"(?:^|(?<=[.!?]\s))(\d+\.\d+)\s+[A-Z]")


def attribute(chunk_text: str, quote: str) -> tuple[str, str]:
    """Find which handbook clause a quote sits in, and the handbook version.

    Both are read out of the retrieved chunk, so neither can be invented. Returns
    ("", "") for a chunk that is not handbook text, such as a tool result.
    """
    numbers = _CLAUSE_IN_CHUNK.findall(chunk_text)
    if not numbers:
        return "", ""
    # Prefer the last clause marker that appears before the quote inside the chunk.
    position = chunk_text.find(quote.strip()[:60])
    chosen = numbers[0]
    if position > 0:
        earlier = [n for n in _CLAUSE_IN_CHUNK.finditer(chunk_text) if n.start() <= position]
        if earlier:
            chosen = earlier[-1].group(1)
    return (chosen if handbook.clause_exists(chosen) else ""), handbook.VERSION


def validate_grounded_answer(output: GroundedAnswer, results, inspection=None):
    issues = []
    if not output.answerable:
        return AnswerResponse(answer=ABSTENTION, confidence="low", abstained=True, retrieved=results,
                              inspection=inspection or {})
    citations, statements = [], []
    # Claims are validated one at a time, and a failing claim is DROPPED rather than allowed
    # to discard the whole answer. A model that writes two well-quoted facts and then one
    # spliced summary sentence should still give you the two facts. If nothing survives we
    # abstain as before. What was dropped is reported in inspection.rejected_claims, so this
    # is visible rather than silent. An injection hit is different in kind: it still poisons
    # the entire answer, because we cannot trust anything drawn from that chunk.
    rejected = []
    for claim in output.claims:
        if claim.context_number > len(results):
            issues.append("Citation refers to a missing context chunk.")
            rejected.append({"statement": claim.statement,
                             "reasons": ["Citation refers to a missing context chunk."]})
            continue
        source = results[claim.context_number - 1]
        if re.search(r"ignore (?:previous|all|your) (?:instructions|rules)|reveal (?:hidden|system) prompts?", source.text, re.I):
            issues.append("Cited context contains a known instruction-override pattern; use other evidence.")
            return AnswerResponse(answer=ABSTENTION, confidence="low", abstained=True, retrieved=results,
                                  validation_issues=sorted(set(issues)), inspection=dict(inspection or {}))
        faults = []
        if normalize(claim.quote) not in normalize(source.text):
            faults.append("Evidence quote does not occur in the cited chunk.")
        if len(normalize(claim.quote)) < 12:
            faults.append("Evidence quote is too short to inspect reliably.")
        if set(re.findall(r"\b\d+(?:\.\d+)?\b", claim.statement)) - set(re.findall(r"\b\d+(?:\.\d+)?\b", claim.quote)):
            faults.append("A numeric claim is absent from its evidence quote.")
        if "SOURCE=" in claim.statement or _CITATION.search(claim.statement):
            faults.append("Claim contains model-generated source labels or citation markers.")
        if faults:
            issues.extend(faults)
            rejected.append({"statement": claim.statement, "reasons": faults})
            continue
        clause, version = attribute(source.text, claim.quote)
        citations.append(Citation(source=source.source, page=source.page, chunk_id=source.id,
                                  number=claim.context_number, url=source_url(source), quote=claim.quote,
                                  clause=clause, handbook_version=version if clause else ""))
        # Attribution is appended by Python, so a Week 6 assertion can require a resolvable
        # section and a handbook version without asking the model for either.
        marker = f" [{claim.context_number}]"
        if clause:
            marker += f" (Handbook {version} Section {clause})"
        statements.append(f"{claim.statement.rstrip()}{marker}")
    calculations = []
    for calculation in output.calculations:
        # Models select supported operands; Python owns the arithmetic and final total.
        # A calculation is all-or-nothing WITHIN itself: one bad operand drops the whole
        # sum, because a partial total would be wrong rather than merely incomplete. It
        # does not drop valid claims alongside it.
        values, refs, seen = [], [], set()
        faults, pending = [], []
        for operand in calculation.operands:
            if operand.context_number > len(results):
                faults.append("Calculation refers to a missing context chunk.")
                continue
            source = results[operand.context_number - 1]
            quote = normalize(operand.quote)
            value = Decimal(str(operand.value))
            numbers = {Decimal(n) for n in re.findall(r"(?<![\w.])-?\d+(?:\.\d+)?(?![\w.])", operand.quote)}
            if numbers != {value}:
                faults.append("Calculation input must match the single numeric value in its evidence quote.")
            # Reuse the source, injection and quote checks used for ordinary claims.
            checked = validate_grounded_answer(GroundedAnswer(answerable=True, claims=[{
                "statement": f"Input: {format(value, 'f')}",
                "context_number": operand.context_number, "quote": operand.quote,
            }]), results)
            # Numeric formatting (20.0 vs 20) is checked by Decimal above instead.
            faults.extend(issue for issue in checked.validation_issues
                          if issue != "A numeric claim is absent from its evidence quote.")
            key = (source.source, quote)
            if key in seen:
                faults.append("Calculation repeats the same evidence; do not double-count it.")
            seen.add(key)
            values.append(value)
            refs.append(operand.context_number)
            pending.append(Citation(source=source.source, page=source.page, chunk_id=source.id,
                                    number=operand.context_number, url=source_url(source), quote=operand.quote))
        if re.search(r"\d|SOURCE=|\[|\]", calculation.label + calculation.unit):
            faults.append("Calculation labels and units cannot contain numbers or citation markers.")
        if len(values) != len(calculation.operands):
            faults.append("Calculation refers to a missing context chunk.")
        if faults:
            issues.extend(faults)
            rejected.append({"statement": f"calculation: {calculation.label}", "reasons": sorted(set(faults))})
            continue
        citations.extend(pending)
        total = sum(values, Decimal(0))
        display = lambda n: format(n.normalize(), "f")
        equation = " + ".join(display(n) for n in values) + " = " + display(total)
        references = " ".join(f"[{n}]" for n in dict.fromkeys(refs))
        statements.append(f"{calculation.label}: {equation} {calculation.unit}. {references}")
        calculations.append({**calculation.model_dump(), "result": display(total)})
    details = dict(inspection or {})
    if calculations:
        details["verified_calculations"] = calculations
    if rejected:
        details["rejected_claims"] = rejected
    # Abstain only when nothing survived validation - not merely because something failed.
    if not statements:
        return AnswerResponse(answer=ABSTENTION, confidence="low", abstained=True, retrieved=results,
                              validation_issues=sorted(set(issues)), inspection=details)
    # Quote membership is deterministic. Entailment still needs semantic review.
    # A partially accepted answer keeps its issues visible and drops to low confidence.
    return AnswerResponse(answer=" ".join(statements), citations=citations,
                          confidence="low" if rejected else "medium",
                          validation_issues=sorted(set(issues)),
                          retrieved=results, inspection=details)
