import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from app.infrastructure.redaction import redact


class TraceLogger:
    def __init__(self, path: Path, names=()):
        self.path = path
        self.names = tuple(names)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def new_trace_id(self) -> str:
        return str(uuid.uuid4())

    def write(self, record: dict[str, Any]) -> None:
        line = json.dumps(redact(record, self.names), ensure_ascii=True, separators=(",", ":"))
        with self._lock, self.path.open("a", encoding="utf-8") as trace_file:
            trace_file.write(line + "\n")

    def recent(self, limit=100):
        """Read a bounded tail; old unredacted records are also sanitized on export."""
        if not self.path.exists(): return []
        with self._lock, self.path.open("rb") as stream:
            size=stream.seek(0,2); start=max(0,size-8_000_000); stream.seek(start)
            if start: stream.readline()
            lines=stream.read(8_000_000).splitlines()
        records=[]
        for line in reversed(lines):
            try: records.append(redact(json.loads(line),self.names))
            except (ValueError,UnicodeError): continue
            if len(records)>=limit: break
        return records

    @staticmethod
    def timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()
