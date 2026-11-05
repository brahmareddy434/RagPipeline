"""Real SDK + local servers for protocol tests; scripted model only for loop boundaries."""
import json
import subprocess
import sys

import pytest
from mcp.types import ListToolsResult, Tool

from app.agents.tools import ToolFailure
from app.infrastructure.mcp.registry import MCPRegistry, ROOT, connect, load_config
from app.services.mcp_host import build_agent


@pytest.mark.asyncio
async def test_discovery_config_only_and_app_attached_resource():
    async with connect(load_config(ROOT / "config/mcp.policy.json")) as first:
        original_names = set(first.tools)
        assert len(original_names) == 2
        assert len(first.resources) == 1
        assert "exclusions" in first.resources[0].text
        assert not any("exclusion" in name for name in first.tools)
        searched = await first.execute("policy__search_policy_documents", {"query": "vehicle damage"})
        assert "7 days" in searched.text
    async with connect(load_config(ROOT / "config/mcp.claims.json")) as both:
        assert set(both.tools) - original_names == {"claims__get_claim_status", "claims__get_adjuster_notes"}
        assert len(both.tools) == 4
        observation = await both.execute("claims__get_claim_status", {"claim_number": "CLM-2024-88120"})
        assert "awaiting repair estimate" in observation.text
        assert observation.evidence[0].source == "mcp:claims__get_claim_status"
        notes = await both.execute("claims__get_adjuster_notes", {"claim_number": "CLM-2024-88120"})
        assert "No coverage decision" in notes.text


@pytest.mark.asyncio
async def test_failures_are_model_readable_not_fake_records():
    async with connect(load_config(ROOT / "config/mcp.claims.json")) as registry:
        with pytest.raises(ToolFailure, match="CLM-YYYY-nnnnn"):
            await registry.execute("claims__get_claim_status", {"claim_number": "88120"})
        with pytest.raises(ToolFailure, match="not found"):
            await registry.execute("claims__get_claim_status", {"claim_number": "CLM-2024-99999"})
        with pytest.raises(ToolFailure, match="required property"):
            await registry.execute("claims__get_claim_status", {})
        with pytest.raises(ToolFailure, match="Unknown discovered tool"):
            await registry.execute("approve_claim", {})
        with pytest.raises(ToolFailure, match="POL-2024-0001"):
            await registry.execute("policy__read_policy", {"policy_number": "POL20240001"})
        result = await registry.execute("policy__read_policy", {"policy_number": "POL-2024-0001"})
        assert "7 days" in result.text


@pytest.mark.asyncio
async def test_before_error_and_after_docstring_are_actually_on_server():
    descriptions = []
    for style in ("before", "after"):
        config = load_config(ROOT / "config/mcp.policy.json")
        config["servers"]["policy"]["args"] += ["--error-style", style]
        async with connect(config) as registry:
            descriptions.append(registry.tools["policy__read_policy"]["tool"].description)
            with pytest.raises(ToolFailure, match="Error 3" if style == "before" else "Retry once"):
                await registry.execute("policy__read_policy", {"policy_number": "POL20240001"})
    assert descriptions[0] == "Read the policy."
    assert "NEXT step" in descriptions[1]


@pytest.mark.asyncio
async def test_wire_is_real_jsonrpc_and_notification_has_no_id(tmp_path):
    config = load_config(ROOT / "config/mcp.claims.json")
    config["servers"].pop("policy")
    async with connect(config, tmp_path) as registry:
        await registry.execute("claims__get_claim_status", {"claim_number": "CLM-2024-88120"})
    records = [json.loads(line) for line in (tmp_path / "claims.jsonl").read_text().splitlines()]
    messages = [json.loads(row["raw"]) for row in records]
    methods = [m["method"] for m in messages if "method" in m]
    assert methods == ["initialize", "notifications/initialized", "tools/list", "tools/call"]
    notification = next(m for m in messages if m.get("method") == "notifications/initialized")
    assert "id" not in notification
    for request in (m for m in messages if "method" in m and "id" in m):
        response = next(m for m in messages if m.get("id") == request["id"] and "result" in m)
        assert response["jsonrpc"] == "2.0"


@pytest.mark.asyncio
async def test_discovery_paginates_and_accepts_unknown_future_tool():
    class PagedSession:
        async def list_tools(self, cursor=None):
            name = "future_tool" if cursor is None else "another_tool"
            return ListToolsResult(tools=[Tool(name=name, description="New capability",
                                    inputSchema={"type": "object"})],
                                   nextCursor="second" if cursor is None else None)

    registry = MCPRegistry()
    await registry.discover("new_server", PagedSession())
    assert registry.names == ("new_server__future_tool", "new_server__another_tool", "finish")
    assert len(registry.discovery) == 2


@pytest.mark.asyncio
async def test_transport_error_distinct_from_missing_record():
    class BrokenSession:
        async def call_tool(self, *args):
            raise TimeoutError()

    registry = MCPRegistry()
    registry.sessions["broken"] = BrokenSession()
    registry.tools["broken__read"] = {"server": "broken", "tool": Tool(name="read", inputSchema={"type": "object"})}
    with pytest.raises(ToolFailure, match="unavailable.*TimeoutError"):
        await registry.execute("broken__read", {})


@pytest.mark.asyncio
async def test_unsafe_remote_url_rejected_before_credentials_sent():
    config = {"servers": {"external": {"transport": "streamable-http", "url": "http://example.com/mcp"}}}
    with pytest.raises(ValueError, match="HTTPS"):
        async with connect(config):
            pass


@pytest.mark.asyncio
async def test_existing_agent_receives_resource_and_discovered_schema():
    from app.agents.memory import Scratchpad
    async with connect(load_config(ROOT / "config/mcp.policy.json")) as registry:
        agent = build_agent(None, registry)
        messages = agent._messages("deadline?", Scratchpad(), [])
        assert "insurance" in messages[0]["content"]
        assert "inputSchema" in messages[0]["content"]
        assert "App-attached context" in messages[1]["content"]
        assert "deliberate damage" in messages[1]["content"]


def test_independent_client_reuses_server():
    run = subprocess.run([sys.executable, "-m", "course.week9_peer_client"], cwd=ROOT,
                         capture_output=True, text=True, timeout=45)
    assert run.returncode == 0, run.stderr
    response = json.loads(run.stdout)
    assert not response["result"]["isError"]
    assert "7 days" in response["result"]["content"][0]["text"]


@pytest.mark.asyncio
async def test_gateway_enforces_scope_and_audits_each_call(monkeypatch, tmp_path):
    import secrets
    status_token, full_token = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    audit = tmp_path / "audit.jsonl"
    for key, value in {"WEEK9_GATEWAY_TOKEN": status_token, "WEEK9_STATUS_TOKEN": status_token,
                       "WEEK9_FULL_TOKEN": full_token, "WEEK9_AUDIT_PATH": str(audit)}.items():
        monkeypatch.setenv(key, value)
    async with connect(load_config(ROOT / "config/mcp.gateway.json")) as registry:
        assert len(registry.tools) == 4
        assert len(registry.resources) == 1
        status = await registry.execute("gateway__claims__get_claim_status", {"claim_number": "CLM-2024-88120"})
        assert "awaiting repair estimate" in status.text
        with pytest.raises(ToolFailure, match="Access denied"):
            await registry.execute("gateway__claims__get_adjuster_notes", {"claim_number": "CLM-2024-88120"})
    rows = [json.loads(line) for line in audit.read_text().splitlines()]
    assert [row["outcome"] for row in rows] == ["ok", "denied"]
    assert all(row["caller"] == "triage-status-demo" for row in rows)
    assert all(row["claim_number"] == "CLM-2024-88120" for row in rows)
    assert status_token not in audit.read_text()
    monkeypatch.setenv("WEEK9_GATEWAY_TOKEN", full_token)
    async with connect(load_config(ROOT / "config/mcp.gateway.json")) as registry:
        notes = await registry.execute("gateway__claims__get_adjuster_notes", {"claim_number": "CLM-2024-88120"})
        assert "Repair estimate requested" in notes.text


def test_gateway_rejects_missing_or_invalid_credentials(monkeypatch):
    from mcp_servers.gateway import identity
    monkeypatch.delenv("WEEK9_GATEWAY_TOKEN", raising=False)
    with pytest.raises(ValueError, match="Missing"):
        identity()
    monkeypatch.setenv("WEEK9_GATEWAY_TOKEN", "not-an-issued-token")
    monkeypatch.setenv("WEEK9_STATUS_TOKEN", "issued-for-this-test")
    monkeypatch.delenv("WEEK9_FULL_TOKEN", raising=False)
    with pytest.raises(ValueError, match="Invalid"):
        identity()


@pytest.mark.asyncio
async def test_same_policy_server_over_streamable_http():
    import asyncio
    import socket
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    process = subprocess.Popen([sys.executable, "-m", "mcp_servers.policy", "--transport",
                                "streamable-http", "--port", str(port)], cwd=ROOT,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(150):
            try:
                reader, writer = await asyncio.open_connection("127.0.0.1", port)
                writer.close()
                await writer.wait_closed()
                break
            except OSError:
                assert process.poll() is None, "HTTP MCP server exited before startup"
                await asyncio.sleep(.1)
        else:
            pytest.fail("HTTP MCP server did not start")
        config = {"servers": {"remote": {"transport": "streamable-http",
                    "url": f"http://127.0.0.1:{port}/mcp", "resources": ["policy://exclusions"]}}}
        async with connect(config) as registry:
            assert len(registry.tools) == 2
            assert len(registry.resources) == 1
            result = await registry.execute("remote__read_policy", {"policy_number": "POL-2024-0001"})
            assert "7 days" in result.text
    finally:
        process.terminate()
        process.wait(timeout=10)


def test_fastapi_discovery_route():
    from fastapi.testclient import TestClient
    from app.main import app
    # This route does not need the HR container or a Chroma/Ollama process.
    response = TestClient(app, client=("127.0.0.1", 50000)).get("/mcp/tools")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == sum(len(p["response"]["tools"]) for p in body["tools_list_responses"])
    assert body["count"] == 4
