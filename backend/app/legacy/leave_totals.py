"""Resolve general annual-leave totals from explicit, unqualified policy facts.

This deliberately narrow rule avoids making a small model decide whether simple
addition is answerable. Unrecognised wording, personal balances, other categories
and conflicting allowances are left to the normal grounded-answer path.
"""
import re

from app.schemas import GroundedAnswer


# Words that carry no meaning for this decision. Stripped before the whitelist check so an
# ordinary phrasing ("... in a year for one employee") is not rejected for containing "for".
# Without this the gate was so tight that only a handful of exact phrasings reached it.
_FILLER = set("""a an the of in on at to for by with and or is are was were be been am
do does did i we you they he she it my our your their his her its one single each any
this that these those there here please tell me give show know about as per if then
kindly want need would could can may want get some much many more most just only also
year years total totals overall altogether combined all""".split())
_GENERAL_WORDS = set("""what is are the a an total count number of leave leaves that
should be any type types all combined altogether how many days do does employees
employee receive get have allowed per year yearly annual allowance allowances and
including include please tell me overall in company policy""".split()) | _FILLER
_ALLOWANCES = (
    re.compile(r"Employees receive (?P<value>\d+(?:\.\d+)?) (?P<category>paid|annual|paid annual) leave days per year\."),
    re.compile(r"The company provides (?P<value>\d+(?:\.\d+)?) days of (?P<category>paid sick|sick) leave every year\."),
)


def annual_leave_total(question, results):
    words = set(re.findall(r"\w+", question.casefold()))
    if not words <= _GENERAL_WORDS or not words & {"leave", "leaves"}:
        return None
    if not words & {"total", "count", "combined", "all", "overall", "altogether"}:
        return None
    facts = {}
    for index, row in enumerate(results, 1):
        # Do not present these two categories as the complete total if other leave
        # categories, overlapping entitlements or conditional rules are mentioned.
        text = row.text
        if not re.search(r"\bleave\b", text, re.I):
            continue
        if re.search(r"\b(?:maternity|paternity|parental|casual|bereavement|unpaid|probation|prorat\w*|including|includes|within|inclusive|except|unless)\b", text, re.I):
            return None
        for pattern in _ALLOWANCES:
            for match in pattern.finditer(text):
                # Only a sentence boundary or an uppercase document heading may
                # precede the fact; e.g. 'Only managers: Employees receive ...'
                # must not become a general employee entitlement.
                prefix = re.split(r"[.!?]", text[:match.start()])[-1].strip()
                if prefix and not (prefix.isupper() and re.fullmatch(r"[A-Z\s-]+", prefix)):
                    return None
                category = "sick" if "sick" in match["category"] else "annual"
                value = float(match["value"])
                if category in facts and facts[category]["value"] != value:
                    return None
                facts.setdefault(category, {"value": value, "context_number": index,
                                            "quote": match.group(0)})
    if set(facts) != {"annual", "sick"}:
        return None
    operands = [facts[category] for category in ("annual", "sick")]
    return GroundedAnswer(answerable=True,
                          claims=[{"statement": operand["quote"],
                                   "context_number": operand["context_number"],
                                   "quote": operand["quote"]} for operand in operands],
                          calculations=[{"label": "Combined annual paid leave and sick leave (excluding carry-forward)",
                                         "unit": "days per year", "operands": operands}])
