from app.repositories.claims import FictionalClaims
from app.agents.claims import ClaimsTools
from app.schemas import AgentRunResponse
from course.claims_trajectories import expectations,assess
from app.services import claims_reports
import json
import pytest

def test_alternative_paths_and_argument_reality_are_independent_of_outcome():
    registry=ClaimsTools(FictionalClaims());case=expectations(registry.repository)[1]
    def run(path):return AgentRunResponse(task='fixture',answer='Under review due to wear.',abstained=False,stop_reason='finished',steps=[{'tool':n,'arguments':{'clause_id' if n=='read_policy_clause' else 'claim_id':a},'ok':True} for n,a in path])
    assert len(case['allowed_paths'])==4
    assert all(assess(run(path),case,registry)['trajectory_pass'] for path in case['allowed_paths'])
    partial=case['allowed_paths'][0][:-1];result=assess(run(partial),case,registry)
    assert result['outcome_pass'] and not result['trajectory_pass'] and result['mode']=='missing_clause'
    fabricated=run([('get_claim_record','CLM-2026-99999')]);result=assess(fabricated,case,registry)
    assert result['argument_validity']==0 and result['mode']=='invalid_arguments'

def test_report_reader_discovers_only_completed_named_phases(tmp_path,monkeypatch):
    monkeypatch.setattr(claims_reports,'ROOT',tmp_path)
    for name in ('baseline-r4','mitigation-r4','baseline-r3','untrusted'):
        path=tmp_path/name;path.mkdir()
        if name!='baseline-r3':(path/'summary.json').write_text(json.dumps({'phase':name}),encoding='utf-8')
    (tmp_path/'mitigation-r4'/'comparison.json').write_text('{"only_change":"one prompt"}',encoding='utf-8')
    report=claims_reports.benchmark_reports()
    assert set(report['reports'])=={'baseline-r4','mitigation-r4'}
    assert report['comparison']['only_change']=='one prompt'
    assert claims_reports.benchmark_case('baseline-r4','agent','C01') is None
    with pytest.raises(ValueError):claims_reports.benchmark_case('../secrets','agent','C01')
