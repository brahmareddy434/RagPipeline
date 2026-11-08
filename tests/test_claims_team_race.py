from types import SimpleNamespace

import pytest

from course.claims_trajectories import expectations
from app.agents.claims import task_for
from app.repositories.claims import FictionalClaims
from course.claims_team_race import freeze_cases, judge_arms
from course.claims_team_race import _percentile99,_verdict,_race_table


def test_freezes_ten_ordered_existing_claims_with_shared_queries_and_provenance():
    cases, manifest = freeze_cases(FictionalClaims())
    assert [case['case_id'] for case in cases] == [f'C{i:02}' for i in range(1, 11)]
    assert [case['claim_id'] for case in cases] == list(FictionalClaims().records)
    assert all(case['task'] == task_for(case['claim_id']) for case in cases)
    assert len(manifest['cohort_sha256']) == 64
    assert len(manifest['judge_sha256']) == 64
    assert manifest['exact_week6_cohort'] is False
    assert 'Week-7/8' in manifest['cohort_provenance']


def test_rejects_changed_or_partial_case_cohort():
    repo = FictionalClaims()
    records = list(repo.records.values())
    with pytest.raises(ValueError, match='exactly ten'):
        freeze_cases(repo, records=records[:9])
    with pytest.raises(ValueError, match='duplicate'):
        freeze_cases(repo, records=[records[0]] * 10)


def test_judges_both_arms_on_identical_case_ids_and_queries(monkeypatch):
    import course.claims_team_race as race
    cases, _ = freeze_cases(FictionalClaims())
    single = [{'case_id': c['case_id'], 'task': c['task'], 'run': SimpleNamespace(task=c['task'])} for c in cases]
    team = [{'case_id': c['case_id'], 'task': c['task'], 'run': SimpleNamespace(task=c['task'])} for c in cases]
    calls = []
    monkeypatch.setattr(race, 'assess', lambda run, case, registry: calls.append((run.task, case['claim_id'])) or {'outcome_pass': True, 'trajectory_pass': True})
    result = judge_arms(single, team, cases, object())
    assert len(calls) == 20
    assert result['single'] == result['team']
    assert result['case_ids'] == [c['case_id'] for c in cases]
    assert calls[:10] == calls[10:]


@pytest.mark.parametrize('arm', ['single', 'team'])
def test_judge_rejects_missing_duplicate_or_mismatched_queries(arm):
    cases, _ = freeze_cases(FictionalClaims())
    single = [{'case_id': c['case_id'], 'task': c['task'], 'run': SimpleNamespace(task=c['task'])} for c in cases]
    team = [{'case_id': c['case_id'], 'task': c['task'], 'run': SimpleNamespace(task=c['task'])} for c in cases]
    with pytest.raises(ValueError):
        judge_arms(single, team[:-1], cases, object())
    target = single if arm == 'single' else team
    target[1]['task'] = 'changed query'
    target[1]['run'].task = 'changed query'
    with pytest.raises(ValueError):
        judge_arms(single, team, cases, object())


def test_nearest_rank_p99_and_verdict_name_sunk_cost_with_multiple_metrics():
    assert _percentile99(list(range(1,101)))==99
    report={"single":{"outcome_pass_rate":.5,"p50_latency_ms":100,"cost_per_claim_usd":.001,
             "p99_latency_ms":400,"total_tokens":1000},"team":{"outcome_pass_rate":.8,
             "p50_latency_ms":300,"cost_per_claim_usd":.002,"p99_latency_ms":900,"total_tokens":2300},
        "context_resend_multiplier":2.3,"dominant_handoff":"manager->coverage_worker","dominant_handoff_share_percent":41,
        "manifest":{"case_ids":[f"C{i:02}" for i in range(1,11)],"cohort_provenance":"provisional"},
        "same_ten_case_ids":[f"C{i:02}" for i in range(1,11)],"model":"fixture","budget":{},
        "execution_order":"alternated"}
    verdict=_verdict(report)
    assert len(verdict.splitlines())<=10 and "Sunk-cost bias" in verdict and "pass rate" in verdict and "cost/claim" in verdict
    table=_race_table(report)
    for metric in ("p50 latency","p99 latency","Total tokens","Mean cost per claim"):assert metric in table


def test_latest_saved_race_only_reads_allowlisted_timestamped_artifacts(tmp_path,monkeypatch):
    import json
    import course.claims_team_race as race
    monkeypatch.setattr(race,"PROJECT_ROOT",tmp_path)
    root=tmp_path/"docs/demos/evidence/claims-team-race"
    old=root/"provisional-week7-8-20261108T090000-000001Z"
    newest=root/"provisional-week7-8-20261108T100000-000001Z"
    malicious=root/"provisional-week7-8-20261108T110000-000001Z-extra"
    for path,label in ((old,"old"),(newest,"new"),(malicious,"malicious")):
        path.mkdir(parents=True)
        (path/"race.json").write_text(json.dumps({"generated_at_utc":label}),encoding="utf-8")
        for name in ("race_table.md","handoffs.log","failure_case.md","verdict.md"):
            (path/name).write_text(label,encoding="utf-8")
    report=race.load_latest_race()
    assert report["generated_at_utc"]=="new"
    assert report["artifacts"]["verdict.md"]=="new"
    assert report["artifacts"]["run_id"]==newest.name
