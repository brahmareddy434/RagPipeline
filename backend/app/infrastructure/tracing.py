import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class TraceLogger:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def new_trace_id(self) -> str:
        return str(uuid.uuid4())

    def write(self, record: dict[str, Any]) -> None:
        line = json.dumps(record, ensure_ascii=True, separators=(",", ":"))
        with self._lock, self.path.open("a", encoding="utf-8") as trace_file:
            trace_file.write(line + "\n")

    @staticmethod
    def timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()
