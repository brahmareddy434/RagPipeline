"""MCP client adapter for the existing PolicyAgent. Tool names are never hard-coded."""
import hashlib
import json
import os
import re
import sys
from contextlib import AsyncExitStack, asynccontextmanager
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlparse

from jsonschema import Draft202012Validator, ValidationError
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client
from app.agent_tools import Observation, ToolFailure, as_evidence

ROOT = Path(__file__).resolve().parents[1]


def load_config(path):
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(config.get("servers"), dict) or not config["servers"]:
        raise ValueError("MCP config needs a nonempty servers object.")
    return config


class MCPRegistry:
    def __init__(self):
        self.tools = {}
        self.sessions = {}
        self.discovery = []
        self.resources = []

    @property
    def names(self):
        return (*self.tools, "finish")

    def catalogue(self):
        lines = [f"- {name}: {item['tool'].description or ''}\n  inputSchema: "
                 + json.dumps(item["tool"].inputSchema, ensure_ascii=False)
                 for name, item in self.tools.items()]
        return "\n".join(lines + ['- finish: Stop when answered or clarification is needed. Arguments: {"summary": "brief conclusion"}.'])

    async def discover(self, server_name, session):
        self.sessions[server_name] = session
        cursor, seen = None, set()
        while True:
            page = await session.list_tools(cursor=cursor)
            self.discovery.append({"server": server_name, "request_cursor": cursor,
                                   "response": page.model_dump(mode="json", by_alias=True, exclude_none=True)})
            for tool in page.tools:
                name = f"{server_name}__{tool.name}"
                if name in self.tools:
                    raise ValueError(f"Duplicate discovered tool: {name}")
                Draft202012Validator.check_schema(tool.inputSchema)
                self.tools[name] = {"server": server_name, "tool": tool}
            cursor = page.nextCursor
            if cursor is None:
                break
            if cursor in seen:
                raise ValueError("Server repeated a tools/list cursor.")
            seen.add(cursor)

    async def execute(self, name, arguments):
        item = self.tools.get(name)
        if item is None:
            raise ToolFailure(f"Unknown discovered tool {name!r}. Choose a listed tool or finish.")
        try:
            Draft202012Validator(item["tool"].inputSchema).validate(arguments)
        except ValidationError as exc:
            raise ToolFailure(f"Invalid arguments for {name}: {exc.message}") from exc
        try:
            result = await self.sessions[item["server"]].call_tool(item["tool"].name, arguments)
        except Exception as exc:
            # A transport failure is not the same as a missing record.
            raise ToolFailure(f"{name} is unavailable ({type(exc).__name__}). Do not infer a record; report unavailability or retry later.") from exc
        text = "\n".join(block.text for block in result.content if block.type == "text")
        if result.isError:
            raise ToolFailure(text or "Tool failed without details; ask for clarification.")
        if not text and result.structuredContent is not None:
            text = json.dumps(result.structuredContent, ensure_ascii=False)
        if not text:
            raise ToolFailure("Tool returned no supported text evidence. Do not invent an answer.")
        key = hashlib.sha256((name + json.dumps(arguments, sort_keys=True) + text).encode()).hexdigest()[:20]
        return Observation(text, [as_evidence(f"mcp:{name}", text, f"mcp-{key}")])


@asynccontextmanager
async def connect(config, wire_dir=None):
    """Config is trusted operator input, never accepted from a user request or model.

    Stdio subprocesses are NOT sandboxed. Remote bearer tokens come only from named
    environment variables and are never written to config or captured on the wire.
    """
    registry = MCPRegistry()
    async with AsyncExitStack() as stack:
        for name, spec in config["servers"].items():
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", name):
                raise ValueError("Server aliases must be simple names (letters, digits, underscore).")
            if spec["transport"] == "stdio":
                command = sys.executable if spec["command"] == "@python" else spec["command"]
                args = list(spec.get("args", []))
                if wire_dir is not None:
                    path = Path(wire_dir).resolve() / f"{name}.jsonl"
                    args = ["-m", "app.mcp_wire", "--output", str(path), "--", command, *args]
                    command = sys.executable
                env = {key: os.environ[key] for key in spec.get("env_names", [])}
                env["PYTHONUTF8"] = "1"
                streams = await stack.enter_async_context(stdio_client(
                    StdioServerParameters(command=command, args=args, env=env, cwd=str(ROOT))))
            elif spec["transport"] == "streamable-http":
                url = spec["url"]
                parsed = urlparse(url)
                if parsed.username or parsed.password or parsed.query or parsed.fragment:
                    raise ValueError("Use a clean MCP URL; credentials belong in the bearer-token environment variable.")
                if parsed.scheme != "https" and not (parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost", "::1"}):
                    raise ValueError("Remote MCP requires HTTPS; plain HTTP is allowed only on loopback.")
                headers = {}
                if spec.get("token_env"):
                    headers["Authorization"] = "Bearer " + os.environ[spec["token_env"]]
                streams = await stack.enter_async_context(streamablehttp_client(url, headers=headers))
            else:
                raise ValueError(f"Unsupported MCP transport: {spec['transport']}")
            session = await stack.enter_async_context(ClientSession(
                streams[0], streams[1], read_timeout_seconds=timedelta(seconds=30)))
            await session.initialize()
            await registry.discover(name, session)
            for uri in spec.get("resources", []):
                result = await session.read_resource(uri)
                text = "\n".join(c.text for c in result.contents if hasattr(c, "text"))
                if not text:
                    raise ValueError(f"Required context resource {uri} returned no text.")
                key = hashlib.sha256(f"{name}:{uri}".encode()).hexdigest()[:20]
                registry.resources.append(as_evidence(f"mcp-resource:{name}:{uri}", text, f"resource-{key}"))
        yield registry
