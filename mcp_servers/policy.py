"""Own reusable server: existing BM25 retrieval, policy lookup, resource, prompt."""
import argparse
import json
import re
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from app.schemas import Chunk
from app.rag.retrieval import KeywordRetriever

from app.config.paths import PROJECT_ROOT as ROOT


def build_server(error_style="after", port=8019):
    server = FastMCP("training-policy-documents", host="127.0.0.1", port=port)
    data = json.loads((ROOT / "course/insurance/policies.json").read_text(encoding="utf-8"))
    policies = data["policies"]
    chunks = [Chunk(id=number, text=text, source=f"policy:{number}", page=None, metadata={})
              for number, text in policies.items()]
    retriever = KeywordRetriever()

    @server.tool()
    def search_policy_documents(query: str) -> str:
        """Search fictional policy documents for a rule or reporting deadline.

        Use a short topic such as 'vehicle damage reporting'. Returns matching source
        text, not an individual claim's status, notes, or a coverage decision.
        """
        if not 2 <= len(query.strip()) <= 300:
            raise ValueError("Use a policy topic between 2 and 300 characters, e.g. vehicle damage.")
        results = retriever.search(query, chunks, k=3)
        return "\n".join(f"[{r.source}] {r.text}" for r in results) or "No matching policy passage. Try another topic or ask for clarification."

    def read_policy(policy_number: str) -> str:
        """Read the policy."""
        if policy_number not in policies:
            if error_style == "before":
                raise ValueError("Error 3")
            compact = re.fullmatch(r"POL(\d{4})(\d{4})", policy_number.upper())
            hint = (f' Retry once by calling read_policy with policy_number="POL-{compact[1]}-{compact[2]}"; '
                    "only separators change. Do not use search_policy_documents to repair this failed lookup."
                    if compact else " Ask the user to confirm the number; do not invent another policy.")
            raise ValueError(f"Policy {policy_number!r} not found. Policy numbers look like POL-YYYY-nnnn.{hint}")
        return policies[policy_number]

    if error_style == "after":
        read_policy.__doc__ = """Read one named policy's exact wording and reporting deadline.
        Choose THIS tool when the question contains a policy number, especially after a
        read_policy error. search_policy_documents is a topic search, not lookup recovery.
        Pass the supplied identifier first. If the error gives a separator-only correction,
        your NEXT step must call THIS tool with the corrected policy_number, once.
        Otherwise ask the user to confirm the identifier. Do not use it for claim status or notes.
        Never guess policy facts after a failed lookup and never decide claim coverage.
        """
    server.tool()(read_policy)

    @server.resource("policy://exclusions", mime_type="text/plain")
    def exclusions() -> str:
        """Context attached by the application; deliberately not a tool."""
        return data["exclusions"]

    @server.prompt()
    def triage_question(claim_number: str) -> str:
        """A user-selected prompt template, not an automatically executed tool."""
        return f"Report the status and outstanding evidence for {claim_number}. Do not decide coverage."

    return server


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--error-style", choices=["before", "after"], default="after")
    parser.add_argument("--transport", choices=["stdio", "streamable-http"], default="stdio")
    parser.add_argument("--port", type=int, default=8019)
    args = parser.parse_args()
    build_server(args.error_style, args.port).run(transport=args.transport)
