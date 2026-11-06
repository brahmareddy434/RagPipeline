import asyncio
import json
import httpx
import pytest
from app.agents.claims import ClaimsTools,ClaimsWorkflow,claims_agent,task_for
from app.repositories.claims import FictionalClaims
from app.domain.tools import ToolFailure
from app.infrastructure.ollama import OllamaClient,call_metrics
from app.infrastructure.budgets import active_budget,ProviderBudget,BudgetExceeded
from app.schemas import AgentBudget,GroundedAnswer

def test_claim_mix_and_status_enum():
    repo=FictionalClaims(); assert len(repo.records)==10
    assert sum(len(r.required_clauses)>1 for r in repo.records.values())>=3
    registry=ClaimsTools(repo)
    assert 'awaiting_documents' in registry.catalogue()
    with pytest.raises(ToolFailure): registry.validate('get_claim_record',{'claim_id':'CLM-2026-10001','status_filter':'approved'})

async def test_reality_checks_and_citable_clauses():
    registry=ClaimsTools(FictionalClaims())
    with pytest.raises(ToolFailure): await registry.execute('get_claim_record',{'claim_id':'CLM-2026-99999'})
    with pytest.raises(ToolFailure): await registry.execute('read_policy_clause',{'clause_id':'EX-FAKE-99'})
    result=await registry.execute('read_policy_clause',{'clause_id':'EX-WEAR-01'})
    assert 'Gradual deterioration' in result.text and result.evidence[0].metadata['origin']=='tool'

async def test_provider_admission_caps_generation_and_blocks_retry():
    provider=OllamaClient('http://fixture','fixture','fixture');await provider.http.aclose();calls=[]
    def handler(request):
        payload=json.loads(request.content);calls.append(payload)
        return httpx.Response(200,json={'message':{'content':'invalid'},'prompt_eval_count':700,'eval_count':200})
    provider.http=httpx.AsyncClient(transport=httpx.MockTransport(handler))
    metrics=[];mt=call_metrics.set(metrics);bt=active_budget.set(ProviderBudget(AgentBudget(max_tokens=1000),metrics))
    try:
        with pytest.raises(BudgetExceeded):await provider.structured([{'role':'user','content':'x'}],GroundedAnswer)
        assert len(calls)<=1
        if calls:assert calls[0]['options']['num_predict']<1200
    finally:active_budget.reset(bt);call_metrics.reset(mt);await provider.close()

async def test_absolute_deadline_cancels_finalization_without_extra_calls():
    class Slow:
        calls=0
        async def structured(self,messages,schema,**kwargs):
            self.calls+=1
            if schema is GroundedAnswer:await asyncio.sleep(10)
            return schema.model_validate({'thought':'lookup','tool':'get_claim_record','arguments':{'claim_id':'CLM-2026-10001'}})
    provider=Slow(); registry=ClaimsTools(FictionalClaims())
    result=await claims_agent(provider,registry).run(task_for('CLM-2026-10001'),budget=AgentBudget(max_steps=1,max_seconds=.05))
    assert result.stop_reason=='timeout' and result.abstained and provider.calls==2
    assert result.usage['latency_ms']<1000

async def test_workflow_has_fixed_three_tool_stages_and_one_generation():
    class Model:
        calls=0
        async def structured(self,messages,schema,**kwargs):self.calls+=1;return GroundedAnswer(answerable=False)
    model=Model(); workflow=ClaimsWorkflow(model,ClaimsTools(FictionalClaims()))
    result=await workflow.run('CLM-2026-10002')
    assert [s['tool'] for s in result.steps]==['get_claim_record','get_adjuster_notes','read_policy_clause','read_policy_clause']
    assert {s['arguments'].get('clause_id') for s in result.steps if s['tool']=='read_policy_clause'}=={'BASE-MOTOR-05','EX-WEAR-01'} and model.calls==1
