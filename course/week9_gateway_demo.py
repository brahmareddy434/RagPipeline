"""Bonus evidence with ephemeral local credentials; never print or save the tokens."""
import argparse
import asyncio
import os
import secrets
from datetime import datetime, timezone

from app.agents.tools import ToolFailure
from app.config.settings import get_settings
from app.infrastructure.mcp.registry import ROOT, connect, load_config
from app.schemas import AgentBudget
from app.infrastructure.ollama import OllamaClient
from app.services.mcp_host import build_agent
from course.week9_demo import save


async def run(live):
    out = ROOT / "course/results/week9-gateway" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out.mkdir(parents=True)
    status_token, full_token = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    values = {"WEEK9_STATUS_TOKEN": status_token, "WEEK9_FULL_TOKEN": full_token,
              "WEEK9_GATEWAY_TOKEN": status_token, "WEEK9_AUDIT_PATH": str(out / "audit.jsonl")}
    previous = {key: os.environ.get(key) for key in values}
    os.environ.update(values)
    settings = get_settings()
    ollama = OllamaClient(settings.ollama_base_url, settings.ollama_chat_model, settings.ollama_embed_model) if live else None
    try:
        async with connect(load_config(ROOT / "config/mcp.gateway.json")) as registry:
            status = await registry.execute("gateway__claims__get_claim_status", {"claim_number": "CLM-2024-88120"})
            try:
                await registry.execute("gateway__claims__get_adjuster_notes", {"claim_number": "CLM-2024-88120"})
            except ToolFailure as exc:
                denial = str(exc)
            else:
                raise AssertionError("Status-only token exposed adjuster notes")
            save(out / "scope_proof.json", {"scope": "status", "status": status.text, "notes_error": denial,
                                            "discovery": registry.discovery})
            if ollama:
                result = await build_agent(ollama, registry).run(
                    "For claim CLM-2024-88120, retrieve its adjuster notes and its current status. "
                    "If notes access is denied, report that restriction and still retrieve the status.",
                    budget=AgentBudget(max_steps=5, max_seconds=600))
                save(out / "model_denial.json", {"model": settings.ollama_chat_model, "run": result.model_dump(mode="json")})
        os.environ["WEEK9_GATEWAY_TOKEN"] = full_token
        async with connect(load_config(ROOT / "config/mcp.gateway.json")) as registry:
            notes = await registry.execute("gateway__claims__get_adjuster_notes", {"claim_number": "CLM-2024-88120"})
            save(out / "full_scope_proof.json", {"scope": "full", "notes": notes.text})
        (out.parent / "latest.txt").write_text(str(out), encoding="utf-8")
        print(f"Gateway evidence: {out}", flush=True)
    finally:
        if ollama:
            await ollama.close()
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    asyncio.run(run(parser.parse_args().live))
