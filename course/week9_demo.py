"""Reproducible Task D evidence. Live model evidence requires --live; never fabricate it."""
import argparse
import asyncio
import difflib
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from app.agents.tools import ToolFailure
from app.config.settings import get_settings
from app.infrastructure.mcp.registry import ROOT, connect, load_config
from app.schemas import AgentBudget
from app.infrastructure.ollama import OllamaClient
from app.services.mcp_host import build_agent

SOURCE_FILES = ("backend/app/agents/loop.py", "backend/app/services/mcp_host.py", "backend/app/infrastructure/mcp/registry.py")
TASK = "What is the current status of claim CLM-2024-88120?"
ANNOTATIONS = {
    "jsonrpc": "JSON-RPC protocol envelope version, exactly 2.0; not the negotiated MCP version.",
    "id": "Request correlation identifier. The response repeats it; notifications have no id.",
    "method": "Operation: initialize negotiates, notifications/initialized confirms readiness, tools/list discovers, tools/call executes.",
    "params": "Operation arguments: initialize has clientInfo/capabilities/protocolVersion; tools/list may have cursor; tools/call has name/arguments.",
    "result": "Successful protocol response: initialize returns server metadata/capabilities; list returns tool schemas; call returns content and isError. isError=true is a recoverable tool failure.",
    "error": "JSON-RPC protocol error (code/message/data), distinct from a successful tools/call response whose result.isError is true.",
}


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def snapshot(directory):
    hashes = {}
    for name in SOURCE_FILES:
        raw = (ROOT / name).read_bytes()
        target = directory / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        hashes[name] = hashlib.sha256(raw).hexdigest()
    return hashes


def summarize(registry):
    # Derived from actual list responses, not the local finish pseudo-tool.
    names = [f"{page['server']}__{tool['name']}" for page in registry.discovery
             for tool in page["response"]["tools"]]
    return {"count": len(names), "names": names, "tools_list_responses": registry.discovery}


async def recovery(ollama, style, out):
    config = load_config(ROOT / "config/mcp.policy.json")
    config["servers"]["policy"]["args"] += ["--error-style", style]
    async with connect(config, out / f"error-{style}-wire") as registry:
        description = registry.tools["policy__read_policy"]["tool"].description
        # Controlled replay establishes exactly the same failing call in both arms.
        # It is explicitly NOT attributed to the model. Subsequent steps are real model output.
        failing = {"tool": "policy__read_policy", "arguments": {"policy_number": "POL20240001"}}
        try:
            await registry.execute(failing["tool"], failing["arguments"])
        except ToolFailure as exc:
            error = str(exc)
        else:
            raise AssertionError("The controlled failing call unexpectedly succeeded.")
        result = None
        if ollama is not None:
            task = ("What is the damage reporting deadline for policy POL20240001? "
                    "A previous tool call was replayed by the test harness, not chosen by you: "
                    + json.dumps(failing) + ". Its actual server error was: " + error
                    + "\nContinue from that error using the tool description. Never guess policy facts.")
            result = (await build_agent(ollama, registry).run(
                task, budget=AgentBudget(max_steps=4, max_seconds=600))).model_dump(mode="json")
        return {"style": style, "description_from_tools_list": description,
                "controlled_failing_call": failing, "actual_error": error,
                "model_run": result, "model_evidence": "live Ollama" if result else "NOT RUN"}


def render_recovery(records):
    text = ["# Same failing call: before / after", "",
            "The harness calls read_policy(POL20240001) in both arms. This first call is controlled, not model-chosen.",
            "Subsequent steps below are unedited live model outputs when --live is used. No improvement is assumed.", ""]
    for item in records:
        text += [f"## {item['style']}", "", "Description returned by tools/list:",
                 "```text", item["description_from_tools_list"], "```", "Actual tools/call error:",
                 "```text", item["actual_error"], "```"]
        run = item["model_run"]
        if run is None:
            text += ["Model transcript NOT RUN. Re-run with --live; this is protocol evidence only.", ""]
        else:
            text += ["Unedited model continuation:", "```json", json.dumps(run, indent=2), "```", ""]
    successes = [len({json.dumps(s["arguments"], sort_keys=True) for s in (r["model_run"] or {}).get("steps", [])
                     if s["ok"] and s["tool"] == "policy__read_policy"}) for r in records]
    text += [f"Unique successful policy reads in the model continuation: {successes[0]} before -> {successes[1]} after (cached repeated steps count once).",
             "If both recover, report that honestly: clearer errors are not proof of an accuracy gain."]
    return "\n".join(text) + "\n"


async def run(live, output):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out = output / stamp
    out.mkdir(parents=True)
    print(f"Evidence: {out}", flush=True)
    settings = get_settings()
    ollama = (OllamaClient(settings.ollama_base_url, settings.ollama_chat_model,
                           settings.ollama_embed_model, settings.ollama_timeout_seconds) if live else None)
    baseline_config = load_config(ROOT / "config/mcp.policy.json")
    claims_config = load_config(ROOT / "config/mcp.claims.json")
    before_hash = snapshot(out / "baseline")
    save(out / "baseline/config.json", baseline_config)
    try:
        async with connect(baseline_config, out / "baseline-wire") as registry:
            before = summarize(registry)
            baseline_probe = await registry.execute("policy__search_policy_documents", {"query": "vehicle damage"})
            save(out / "baseline_probe.json", {"observation": baseline_probe.text})
        print(f"Server one: {before['count']} tools discovered.", flush=True)

        # Server-two addition: use the same frozen Python modules, change config only.
        async with connect(claims_config, out / "claims-wire") as registry:
            after = summarize(registry)
            status = await registry.execute("claims__get_claim_status", {"claim_number": "CLM-2024-88120"})
            notes = await registry.execute("claims__get_adjuster_notes", {"claim_number": "CLM-2024-88120"})
            save(out / "protocol_probe.json", {"kind": "direct SDK calls, not model-selected",
                                               "status": status.text, "notes": notes.text})
            if ollama:
                print("Running live model query through discovered claims tool...", flush=True)
                run_result = await build_agent(ollama, registry).run(TASK, budget=AgentBudget(max_seconds=600))
                save(out / "claim_query.json", {"model": settings.ollama_chat_model, "run": run_result.model_dump(mode="json")})
            else:
                save(out / "claim_query.json", {"model_evidence": "NOT RUN; use --live", "task": TASK})
        after_hash = snapshot(out / "with_claims")
        save(out / "with_claims/config.json", claims_config)
        diff_chunks = []
        for name in SOURCE_FILES:
            command = ["git", "diff", "--no-index", "--", f"baseline/{name}", f"with_claims/{name}"]
            completed = subprocess.run(command, cwd=out, capture_output=True, text=True)
            if completed.returncode not in (0, 1):
                raise RuntimeError(completed.stderr)
            diff_chunks += ["$ " + " ".join(command), completed.stdout or "(empty git diff; 0 changed lines)"]
        (out / "agent_diff.txt").write_text(
            "Scope: Week 9 server-one baseline -> same agent with server two.\n"
            "This is NOT a claim of zero Week 8 -> Week 9 integration changes.\n"
            + "\n".join(diff_chunks) + "\n", encoding="utf-8")
        assert before_hash == after_hash, "Host/agent source changed during the config-only experiment."
        save(out / "source_hashes.json", {"baseline": before_hash, "with_claims": after_hash})
        diff = difflib.unified_diff(json.dumps(baseline_config, indent=2).splitlines(True),
                                    json.dumps(claims_config, indent=2).splitlines(True),
                                    fromfile="config/mcp.policy.json", tofile="config/mcp.claims.json")
        (out / "config_diff.txt").write_text("".join(diff), encoding="utf-8")
        save(out / "tool_counts.json", {"before": before, "after": after, "finish_excluded": True})
        print(f"Discovery: {before['count']} -> {after['count']}; agent diff: 0 changed lines.", flush=True)
        records = []
        for style in ("before", "after"):
            print(f"Error recovery {style} ({'live model' if live else 'protocol only'})...", flush=True)
            record = await recovery(ollama, style, out)
            records.append(record)
            save(out / f"error_{style}.json", record)
        (out / "error_before_after.md").write_text(render_recovery(records), encoding="utf-8")
        exchanges = []
        for line in (out / "claims-wire/claims.jsonl").read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            message = json.loads(row["raw"])
            exchanges.append({**row, "message": message,
                              "annotations": {key: ANNOTATIONS[key] for key in message}})
        save(out / "wire.json", {"source": "actual local stdio bytes captured by app.infrastructure.mcp.wire; raw preserves each line",
             "annotation_note": "Authored explanations supplied for study; student must review and explain them personally.",
             "model_location": "Ollama runs in the host via backend/app/agents/loop.py -> backend/app/infrastructure/ollama.py; initialize, tools/list, tools/call and both servers make no model calls.",
             "exchanges": exchanges})
        (out / "risk_note.md").write_text(
            "Author: this repository's locally authored fictional claims stand-in; actual platform vendor/provenance not supplied.\n"
            "Reach: reads fixture claims/notes; no outbound network code, but stdio runs with the launching user's OS permissions, not a sandbox.\n"
            "Logs: SDK method diagnostics on stderr; this opt-in demo records full tool arguments/results locally, so use fictional data only.\n"
            "Stolen token: this stdio fixture has no token; a real read token could expose every claim/note in its scope, so require least privilege.\n"
            "Decision: ship for local coursework only; do not connect real claims until provenance, scopes, isolation, logging and retention are verified.\n",
            encoding="utf-8")
        save(out / "manifest.json", {"created_utc": stamp, "live_model": live,
             "model": settings.ollama_chat_model if live else None, "claims_server": "local fictional stand-in",
             "agent_changed_lines": 0, "tools_before": before["count"], "tools_after": after["count"]})
        (output / "latest.txt").write_text(str(out.resolve()), encoding="utf-8")
        print(f"Completed. Open {out / 'manifest.json'}", flush=True)
    finally:
        if ollama:
            await ollama.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--output", type=Path, default=ROOT / "course/results/week9")
    args = parser.parse_args()
    asyncio.run(run(args.live, args.output))
