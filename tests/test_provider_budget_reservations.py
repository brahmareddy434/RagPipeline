import pytest
import httpx

from app.infrastructure.budgets import BudgetExceeded, ProviderBudget
from app.schemas import AgentBudget
from app.infrastructure.ollama import OllamaClient,call_metrics
from app.infrastructure.budgets import active_budget


def test_concurrent_admissions_reserve_upper_bound_before_awaited_call():
    metrics=[]
    guard=ProviderBudget(AgentBudget(max_tokens=1000,max_cost_usd=1),metrics)
    payload={"model":"fixture","messages":[{"role":"user","content":"x"*100}] ,"options":{"num_predict":700}}
    first=guard.admit("/api/chat",payload)
    assert len(first)==4 and first[2] <= 1000-first[1]
    with pytest.raises(BudgetExceeded):
        guard.admit("/api/chat",payload)
    guard.settle(first[3],first[1],first[2])
    assert not guard._pending


def test_settle_is_idempotent_and_non_chat_endpoints_are_unreserved():
    guard=ProviderBudget(AgentBudget(),[])
    assert guard.admit("/api/tags",None)==(None,0,0,None)
    request=guard.admit("/api/chat",{"messages":[{"content":"x"}],"options":{"num_predict":2}})
    guard.settle(request[3],request[1],1)
    guard.settle(request[3],request[1],1)
    assert not guard._pending


@pytest.mark.asyncio
async def test_unexpected_transport_exception_releases_admission_reservation():
    client=OllamaClient("http://fixture","fixture","fixture")
    await client.close()
    client.http=httpx.AsyncClient(transport=httpx.MockTransport(lambda request: (_ for _ in ()).throw(RuntimeError("fixture failure"))))
    metrics=[];guard=ProviderBudget(AgentBudget(max_tokens=2000),metrics)
    budget_token=active_budget.set(guard);metrics_token=call_metrics.set(metrics)
    try:
        with pytest.raises(RuntimeError):
            await client.chat([{"role":"user","content":"bounded"}])
        assert not guard._pending
    finally:
        active_budget.reset(budget_token);call_metrics.reset(metrics_token);await client.close()
