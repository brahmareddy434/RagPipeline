import pytest

from app.agents.claims import task_for
from app.agents.claims_team import ClaimsTeam, SpecialistNote, WorkPlan
from app.repositories.claims import FictionalClaims
from app.agents.claims import ClaimsTools
from app.schemas import AgentBudget
from app.infrastructure.ollama import provider_call_group
from course.claims_trajectories import expectations,assess


class PlanningOnly:
    async def structured(self, messages, schema, **kwargs):
        assert schema is WorkPlan
        return WorkPlan(coverage_scope="Check status and cited exclusions.",notes_scope="Extract unresolved items.")


@pytest.mark.asyncio
async def test_injected_coverage_500_abstains_and_records_failure_without_claiming_coverage():
    team=ClaimsTeam(PlanningOnly(),ClaimsTools(FictionalClaims()))
    result=await team.run("CLM-2026-10001",AgentBudget(max_steps=6,max_tokens=4000,max_seconds=3),fail_coverage=True)
    assert result.task==task_for("CLM-2026-10001")
    assert result.stop_reason=="worker_error" and result.abstained
    assert "undetermined" in result.answer.lower()
    assert result.usage["worker_failures"]==[{"worker":"coverage/exclusions","status_code":500,"injection":"in-process Week 10 fault fixture"}]
    assert [s["tool"] for s in result.steps]==["get_claim_record","get_adjuster_notes","read_policy_clause"]


@pytest.mark.asyncio
async def test_manager_accepts_only_specialist_quotes_that_validate_and_passes_same_judge():
    registry=ClaimsTools(FictionalClaims());record=registry.repository.get("CLM-2026-10001")
    record_quote=f"Claim {record.claim_id} status is {record.status.value}."
    note_quote=record.notes[0]
    clause_quote=registry.repository.clause("DOCS-MOTOR-09")
    class TeamModel:
        calls=0
        async def structured(self,messages,schema,**kwargs):
            self.calls+=1
            group=provider_call_group.get()
            if schema is WorkPlan:return WorkPlan(coverage_scope="Check status and exclusion wording.",notes_scope="Find unresolved items.")
            if group=="manager->coverage_worker":return SpecialistNote(summary="Status and policy evidence.",source_quotes=[record_quote,clause_quote])
            if group=="manager->notes_worker":return SpecialistNote(summary="The estimate is missing.",unresolved=["repair estimate"],source_quotes=[note_quote])
            raise AssertionError(f"Unexpected model stage: {group}")
    model=TeamModel()
    result=await ClaimsTeam(model,registry).run("CLM-2026-10001",AgentBudget(max_steps=6,max_tokens=5000,max_seconds=5))
    assert not result.abstained, (result.stop_reason,result.stop_detail,result.validation_issues)
    assert "awaiting_documents" in result.answer and "repair estimate is missing" in result.answer
    assert len(result.citations)==3
    case=next(c for c in expectations(registry.repository) if c["claim_id"]=="CLM-2026-10001")
    score=assess(result,case,registry)
    assert score["outcome_pass"] and score["trajectory_pass"]
    assert model.calls==3 and result.usage["model_calls"]==0
