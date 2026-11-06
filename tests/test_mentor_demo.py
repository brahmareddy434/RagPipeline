from contextlib import asynccontextmanager
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.controllers import claims, mcp
from app.services import mentor_demo, mcp_host
from app.services.mentor_demo import DemoClaimsTools, MentorDemo, INJECTION_NOTE
from app.repositories.claims import FictionalClaims
from app.schemas import AgentBudget, AgentRunResponse


async def test_injection_is_delivered_through_notes_without_mutating_repository():
    repo = FictionalClaims()
    original = repo.get('CLM-2026-10004').notes
    injected = DemoClaimsTools(repo, 'CLM-2026-10004', True)
    clean = DemoClaimsTools(repo, 'CLM-2026-10004', False)
    args = {'claim_id': 'CLM-2026-10004'}
    record = await injected.execute('get_claim_record', args)
    assert not injected.injection_delivered and INJECTION_NOTE not in record.text
    note = await injected.execute('get_adjuster_notes', args)
    assert injected.injection_delivered and INJECTION_NOTE in note.text
    assert any(e.text == INJECTION_NOTE for e in note.evidence)
    assert INJECTION_NOTE not in (await clean.execute('get_adjuster_notes', args)).text
    assert repo.get(args['claim_id']).notes == original
    with pytest.raises(ValueError, match='scoped'):
        await injected.execute('get_adjuster_notes', {'claim_id': 'CLM-2026-10001'})


async def test_demo_uses_identical_query_budget_and_only_changes_mitigation(monkeypatch):
    calls = []

    def factory(provider, registry, mitigation=False):
        class Runner:
            async def run(self, task, budget):
                calls.append((task, budget, mitigation))
                return AgentRunResponse(task=task, answer='Under review.', stop_reason='finished', steps=[
                    {'tool': 'get_claim_record', 'arguments': {'claim_id': registry.claim_id}, 'ok': True},
                    {'tool': 'get_claim_record', 'arguments': {'claim_id': registry.claim_id}, 'ok': True},
                ])
        return Runner()

    monkeypatch.setattr(mentor_demo, 'claims_agent', factory)
    demo = MentorDemo(object(), FictionalClaims())
    task = 'What is unresolved for CLM-2026-10004?'
    budget = AgentBudget()
    b = await demo.run(task, 'before', True, budget)
    a = await demo.run(task, 'after', True, budget)
    assert calls == [(task, budget, False), (task, budget, 'invalid_arguments')]
    assert a['diagnostics']['repeated_calls'] == 1
    assert not b['diagnostics']['injection_delivered']  # No notes call, not a security pass.
    for bad in ['No ID', 'CLM-2026-10001 and CLM-2026-10002', 'CLM-2026-99999']:
        with pytest.raises(ValueError):
            await demo.run(bad, 'before', False, budget)


def test_demo_api_validates_and_uses_fixed_budget(monkeypatch):
    calls = []
    class Demo:
        async def run(self, *args):
            calls.append(args)
            return {'task': args[0], 'variant': args[1], 'run': {}}
    monkeypatch.setattr(claims, 'container', lambda request: SimpleNamespace(mentor_demo=Demo()))
    async def trace(*args): return 'demo-trace'
    monkeypatch.setattr(claims, '_trace', trace)
    app = FastAPI(); app.include_router(claims.router)
    with TestClient(app) as client:
        payload = {'task': 'Check CLM-2026-10004', 'variant': 'after', 'injection': True}
        reply = client.post('/claims/demo/run', json=payload)
        assert reply.status_code == 200 and reply.json()['trace_id'] == 'demo-trace'
        assert calls[0][:3] == (payload['task'], 'after', True)
        assert calls[0][3].max_seconds == 180 and calls[0][3].max_tokens == 32000
        assert client.post('/claims/demo/run', json={**payload, 'variant': 'other'}).status_code == 422
        assert client.post('/claims/demo/run', json={**payload, 'budget': {'max_tokens': 200000}}).status_code == 422
        assert client.post('/claims/demo/run', json={**payload, 'task': 'x' * 2001}).status_code == 422


def test_mcp_demo_only_selects_allowlisted_configs_and_preserves_task(monkeypatch):
    calls = []
    async def run(task, config_path=None, budget=None):
        calls.append((task, config_path, budget))
        return {'run': {}, 'discovery': []}
    async def trace(*args): return 'mcp-trace'
    monkeypatch.setattr(mcp_host, 'run_task', run)
    monkeypatch.setattr(mcp, '_trace', trace)
    app = FastAPI(); app.include_router(mcp.router)
    with TestClient(app) as client:
        for variant in ['before', 'after']:
            reply = client.post('/mcp/demo/run', json={'task': 'Status CLM-2024-88120?', 'variant': variant})
            assert reply.status_code == 200 and reply.json()['variant'] == variant
        assert client.post('/mcp/demo/run', json={'task': 'Status?', 'variant': '../../private'}).status_code == 422
        assert client.get('/mcp/demo/tools?variant=unknown').status_code == 422
    assert calls[0][0] == calls[1][0] and calls[0][2] == calls[1][2]
    assert calls[0][1].name == 'mcp.policy.json' and calls[1][1].name == 'mcp.claims.json'
    with pytest.raises(ValueError): mcp_host.demo_config('../secret')


async def test_mcp_demo_discovery_reports_actual_registry(monkeypatch):
    paths = []
    @asynccontextmanager
    async def connect(config):
        paths.append(config)
        yield SimpleNamespace(tools={'policy__read_policy': object()}, discovery=[{'actual': True}])
    monkeypatch.setattr(mcp_host, 'load_config', lambda path: path)
    monkeypatch.setattr(mcp_host, 'connect', connect)
    result = await mcp_host.demo_discovery('before')
    assert result['count'] == 1 and result['names'] == ['policy__read_policy']
    assert result['tools_list_responses'] == [{'actual': True}]
    assert paths[0].name == 'mcp.policy.json'
