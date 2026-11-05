import json
import pytest
from app.infrastructure.tracing import TraceLogger
from course.claims_review import sample

def test_prewrite_redacts_nested_fields_raw_outputs_errors_and_keys(tmp_path):
    path=tmp_path/"private.jsonl"; logger=TraceLogger(path,names=["Jane Example"])
    logger.write({"claimant_name":"Alex Sample","CLM-2024-88120":{"raw":"Jane Example / Alex Sample / CLM-2024-88120"},
                  "error":"Bearer secret-credential jane@example.test","token":"private-secret"})
    raw=path.read_text()
    for forbidden in ["Alex Sample","Jane Example","88120","secret-credential","jane@example.test","private-secret"]:
        assert forbidden not in raw
    assert "[CLAIM_ID]" in raw and "[REDACTED]" in raw

def test_recent_trace_reader_is_bounded_and_redacts_old_records(tmp_path):
    path=tmp_path/"old.jsonl"; path.write_text('\n'.join(json.dumps({"trace_id":str(i),"error":"CLM-2024-88120"}) for i in range(150)))
    rows=TraceLogger(path).recent(20)
    assert len(rows)==20 and rows[0]["trace_id"]=="149" and rows[0]["error"]=="[CLAIM_ID]"

def test_seeded_sampling_reproducible_over_1000_records_without_notes(tmp_path):
    log=tmp_path/"traces.jsonl"; log.write_text('\n'.join(json.dumps({"trace_id":str(i)}) for i in range(1100)))
    sample(log,tmp_path/"one",42); sample(log,tmp_path/"two",42)
    assert (tmp_path/"one/sample.json").read_bytes()==(tmp_path/"two/sample.json").read_bytes()
    assert all(not row["human_observation"] for row in json.loads((tmp_path/"one/observations.json").read_text()))
    with pytest.raises(ValueError): sample(log,tmp_path/"one",42)
