import json
import pytest
from app.services.claims_evaluation import assertions,evaluate,training_cases,JUDGE_V1
from course.claims_evaluation import seal,validate_seal,committed

@pytest.mark.parametrize("value",[True,float('nan'),float('inf'),-1,"500"])
def test_deductible_requires_finite_nonnegative_number(value):
    summary=training_cases()[0]["summary"];summary["deductible"]=value
    assert not assertions(summary,set())["numeric_deductible"]

def test_real_dates_and_real_clause_ids():
    summary=training_cases()[0]["summary"];summary.update(date_of_loss="2026-02-30",denied=True,denial_clause="EX-FAKE-99")
    result=assertions(summary,{"EX-WEAR-01"})
    assert not result["date_of_loss"] and not result["denial_clause"]
    summary.update(date_of_loss="2024-02-29",denial_clause="EX-WEAR-01")
    assert all(assertions(summary,{"EX-WEAR-01"}).values())

def test_mode_report_does_not_pass_overclaims_as_judged():
    report=evaluate(); assert len(report["cases"])==30 and len(report["modes"])==6
    assert report["modes"]["invalid_id"]["passed"]==0
    assert report["modes"]["coverage_overclaim"]["passed"]==5
    assert all(r["judge"].startswith("pending") for r in report["cases"])
    assert all(word not in JUDGE_V1.lower() for word in ["deductible","date of loss","claim id","denial clause"])

def test_seal_rejects_tampering_and_requires_commit(tmp_path):
    labels=tmp_path/"labels.json"; receipt=tmp_path/"sealed.json"
    labels.write_text(json.dumps({f"E{i:02}":True for i in range(1,26)}))
    seal(labels,receipt); validate_seal(receipt)
    data=json.loads(receipt.read_text()); data["labels"]["E01"]=False;receipt.write_text(json.dumps(data))
    with pytest.raises(ValueError): validate_seal(receipt)
    with pytest.raises(ValueError): committed(receipt)
