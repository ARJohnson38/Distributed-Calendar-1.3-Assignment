from __future__ import annotations
import json
import os
import threading
from datetime import datetime, timezone

class JsonlLogger:
    def __init__(self, node_id: int, path: str):
        self.node_id = node_id
        self.path = path
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(path), exist_ok=True)

    @staticmethod
    def utc_now() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

    def write(self, action: str, **fields) -> None:
        record = {
            "wall_time_utc": self.utc_now(),
            "node_id": self.node_id,
            "action": action,
            **fields,
        }
        line = json.dumps(record, sort_keys=True)
        with self._lock:
            with open(self.path, "a", encoding="utf-8") as handle:
                handle.write(line + "\n")
