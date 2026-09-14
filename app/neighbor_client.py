from __future__ import annotations
import json
import socket
import time

def send_request(host: str, port: int, message: dict, timeout: float = 10.0, retries: int = 5) -> dict:
    payload = (json.dumps(message) + "\n").encode("utf-8")
    last_error = None
    for attempt in range(retries):
        try:
            with socket.create_connection((host, port), timeout=timeout) as sock:
                sock.sendall(payload)
                file_obj = sock.makefile("r", encoding="utf-8")
                line = file_obj.readline()
                if not line:
                    raise ConnectionError("peer closed without response")
                return json.loads(line)
        except OSError as exc:
            last_error = exc
            time.sleep(min(1 + attempt, 3))
    raise ConnectionError(f"unable to contact {host}:{port}: {last_error}")
