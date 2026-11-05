import json
import uuid

from app.infrastructure.tracing import TraceLogger


def test_trace_logger_appends_jsonl_with_uuid(tmp_path):
    logger = TraceLogger(tmp_path / "ask_traces.jsonl")
    trace_id = logger.new_trace_id()
    uuid.UUID(trace_id)

    logger.write({"trace_id": trace_id, "status": "completed"})
    logger.write({"trace_id": logger.new_trace_id(), "status": "failed"})

    lines = (tmp_path / "ask_traces.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["trace_id"] == trace_id
