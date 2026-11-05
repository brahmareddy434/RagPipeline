"""Optional bonus: one stdio front door, dynamic routing, process-scoped tokens, audit.

This is a local teaching gateway, not an OAuth resource server. The operator passes
credentials via environment variables; the model never receives them.
"""
import asyncio
import hmac
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator
from mcp.server.lowlevel import Server
from mcp.server.lowlevel.helper_types import ReadResourceContents
from mcp.server.stdio import stdio_server
from mcp.types import CallToolResult, Resource, TextContent
from app.mcp_registry import ROOT, connect, load_config


def identity():
    token = os.environ.get("WEEK9_GATEWAY_TOKEN", "")
    if not token:
        raise ValueError("Missing gateway credential; supply WEEK9_GATEWAY_TOKEN in the process environment.")
    for scope, variable in (("full", "WEEK9_FULL_TOKEN"), ("status", "WEEK9_STATUS_TOKEN")):
        expected = os.environ.get(variable, "")
        if expected and hmac.compare_digest(token, expected):
            return scope
    raise ValueError("Invalid gateway credential.")


async def main():
    scope = identity()
    access = json.loads((ROOT / "config/gateway.scopes.json").read_text(encoding="utf-8"))[scope]
    audit_path = Path(os.environ["WEEK9_AUDIT_PATH"])
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    async with connect(load_config(ROOT / "config/mcp.claims.json")) as upstream:
        gateway = Server("training-claims-gateway")

        @gateway.list_tools()
        async def list_tools():
            # No registration table: return the live upstream schemas under stable aliases.
            return [item["tool"].model_copy(update={"name": name}) for name, item in upstream.tools.items()]

        @gateway.list_resources()
        async def list_resources():
            return [Resource(uri="policy://exclusions", name="Policy exclusions", mimeType="text/plain")]

        @gateway.read_resource()
        async def read_resource(uri):
            if str(uri) != "policy://exclusions":
                raise ValueError("Unknown resource")
            return [ReadResourceContents(content=e.text, mime_type="text/plain") for e in upstream.resources]

        @gateway.call_tool(validate_input=False)
        async def call_tool(name, arguments):
            outcome = "error"
            try:
                if name not in access["tools"]:
                    outcome = "denied"
                    return CallToolResult(isError=True, content=[TextContent(type="text", text=(
                        f"Access denied for {name}: caller {access['caller']} has status-only scope. "
                        "Claim status is permitted. Do not infer adjuster notes; report the restriction and request authorized access."))])
                item = upstream.tools[name]
                Draft202012Validator(item["tool"].inputSchema).validate(arguments)
                result = await upstream.sessions[item["server"]].call_tool(item["tool"].name, arguments)
                outcome = "tool_error" if result.isError else "ok"
                return result
            except Exception as exc:
                return CallToolResult(isError=True, content=[TextContent(type="text", text=f"Gateway call failed ({type(exc).__name__}); check arguments or retry later. Do not infer a claim.")])
            finally:
                # Exactly one audit line per attempted call, including denials and failures.
                with audit_path.open("a", encoding="utf-8") as log:
                    log.write(json.dumps({"time": datetime.now(timezone.utc).isoformat(),
                        "caller": access["caller"], "tool": name,
                        "claim_number": arguments.get("claim_number"), "outcome": outcome}) + "\n")

        async with stdio_server() as (read, write):
            await gateway.run(read, write, gateway.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
