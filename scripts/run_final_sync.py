import json
import socket
import time

NODE_COUNT = 10
ROUNDS = 6

def request_port(port: int, message: dict, timeout: float = 20.0) -> dict:
    with socket.create_connection(("127.0.0.1", port), timeout=timeout) as sock:
        sock.sendall((json.dumps(message) + "\n").encode())
        line = sock.makefile("r", encoding="utf-8").readline()
        if not line:
            raise RuntimeError("no response")
        return json.loads(line)

print("Waiting for all schedulers to complete...")
while True:
    statuses = []
    for node_id in range(NODE_COUNT):
        statuses.append(request_port(8001 + node_id, {"type": "STATUS"}))
    completed = sum(bool(s.get("scheduler_complete")) for s in statuses)
    sizes = [s.get("calendar_size") for s in statuses]
    print(f"Schedulers complete: {completed}/10; calendar sizes={sizes}")
    if completed == NODE_COUNT:
        break
    time.sleep(10)

for round_number in range(1, ROUNDS + 1):
    print(f"Starting final synchronization round {round_number}/{ROUNDS}")
    for node_id in range(NODE_COUNT):
        result = request_port(
            8001 + node_id,
            {"type": "FINAL_SYNC", "round": round_number},
            timeout=30,
        )
        if not result.get("ok"):
            raise RuntimeError(result)
    time.sleep(2)

print("Final synchronization complete.")
