"""The handbook as structured data: version, sections, and jurisdiction annexes.

Two graded requirements depend on this being a lookup rather than a model call.

Week 6 asks for criteria moved *out* of the LLM judge and into deterministic assertions.
Two of those criteria are "a policy section reference is present and resolves to a real
section" and "the handbook version is cited". Both are a dictionary lookup, so paying a
model to check them would be paying for something `if` does for free and never gets wrong.

Week 7 asks for a third tool with an enum parameter. `JURISDICTIONS` is that enum, and it
is derived from the annex headings, so the tool's allowed values cannot drift away from
the documents.
"""
import re
from functools import lru_cache
from pathlib import Path

from app.config.paths import PROJECT_ROOT as ROOT
HANDBOOK_DIR = ROOT / "course" / "handbook"
VERSION = "v3.2"
EFFECTIVE_FROM = "2026-01-01"

# "**2.3 Planned leave notice, under two years of service.** An employee with ..."
_CLAUSE = re.compile(r"^\*\*(?P<number>\d+\.\d+)\s+(?P<title>[^*]+?)\*\*\s*(?P<body>.*)$")
_ANNEX = re.compile(r"^\*\*(?P<number>9\.\d+)\s+(?P<name>[^(]+)\((?P<code>[A-Z]{2})\)\.\*\*")


@lru_cache(maxsize=1)
def clauses() -> dict[str, dict[str, str]]:
    """Every numbered clause in the handbook, keyed by its number, e.g. '2.3'."""
    found: dict[str, dict[str, str]] = {}
    for path in sorted(HANDBOOK_DIR.glob("section-*.md")):
        for line in path.read_text(encoding="utf-8").splitlines():
            match = _CLAUSE.match(line.strip())
            if match:
                found[match["number"]] = {
                    "number": match["number"],
                    "title": match["title"].rstrip(". "),
                    "text": match["body"].strip(),
                    "source": path.name,
                }
    return found


def clause_exists(number: str) -> bool:
    """Does this section reference resolve to a real clause? A lookup, not an opinion."""
    return number.strip() in clauses()


@lru_cache(maxsize=1)
def jurisdictions() -> tuple[str, ...]:
    """The jurisdiction codes the handbook actually has an annex for."""
    codes = []
    for path in sorted(HANDBOOK_DIR.glob("section-9-*.md")):
        for line in path.read_text(encoding="utf-8").splitlines():
            match = _ANNEX.match(line.strip())
            if match and match["code"] not in codes:
                codes.append(match["code"])
    return tuple(codes)


def annex(code: str) -> dict[str, str] | None:
    """The annex clause for one jurisdiction code, or None if the handbook has no annex."""
    code = code.strip().upper()
    for number, clause in clauses().items():
        if number.startswith("9.") and f"({code})" in clause["title"]:
            return clause
    return None


def cited_clauses(text: str) -> list[str]:
    """Section references that appear in an answer, e.g. 'Section 2.3' or '§2.3'."""
    return re.findall(r"(?:Section|section|§)\s*(\d+\.\d+)", text)


def cites_version(text: str) -> bool:
    """Is the handbook version stated? Accepts 'v3.2' or 'version 3.2'."""
    return bool(re.search(rf"\bv{re.escape(VERSION.lstrip('v'))}\b|version\s+{re.escape(VERSION.lstrip('v'))}\b",
                          text, re.I))


def files() -> list[tuple[str, bytes]]:
    """The handbook as (filename, bytes) pairs, ready for the ingestion service."""
    return [(p.name, p.read_bytes()) for p in sorted(HANDBOOK_DIR.glob("*.md"))]
