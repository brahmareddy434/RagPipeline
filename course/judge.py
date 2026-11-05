"""The policy-answer judge: one binary criterion, prompt loaded from a versioned file.

Everything a rule can settle was moved into `app/week6_assertions.py`, so this judge is
left with the single criterion that needs reading comprehension. That is deliberate:

* a rule is free, instant and never has an off day, so it should run first;
* a binary verdict can be validated against a human and used as a release gate, whereas a
  1-10 score cannot be calibrated by a small model and tempts a "within 1 is a match"
  tolerance that inflates agreement into meaninglessness.

The prompt lives in evaluation/week6/judge_v1.txt and judge_v2.txt so the two versions can
be diffed, and so iterating the prompt does not mean editing code.
"""
import json
from pathlib import Path

from pydantic import BaseModel, Field

from app.config.paths import PROJECT_ROOT as ROOT
PROMPT_DIR = ROOT / "evaluation" / "week6"


class Grade(BaseModel):
    """The judge's whole output. Binary, with the evidence it relied on."""
    passed: bool
    explanation: str = Field(min_length=1, max_length=800)


def load_prompt(version: str = "v1") -> str:
    path = PROMPT_DIR / f"judge_{version}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Missing judge prompt {path}. judge_v2.txt is written by agreement.py.")
    return path.read_text(encoding="utf-8")


class PolicyAnswerJudge:
    """Grades one answer on one criterion. Knows nothing about assertions."""

    def __init__(self, ollama, version: str = "v1"):
        self.ollama = ollama
        self.version = version
        self.prompt = load_prompt(version)

    async def grade(self, question: str, answer: str, contexts: list[str]) -> dict:
        result = await self.ollama.structured([
            {"role": "system", "content": self.prompt},
            {"role": "user", "content": json.dumps(
                {"question": question, "answer": answer, "handbook_context": contexts},
                ensure_ascii=False)},
        ], Grade, temperature=0)
        return {"passed": result.passed, "explanation": result.explanation,
                "judge_version": self.version}
