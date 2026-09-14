import json
import socket
import time

NODE_COUNT = 10
PORT = 8000

def request(host, message, timeout=2):
    with socket.create_connection((host, PORT), timeout=timeout) as sock:
        sock.sendall((json.dumps(message) + "\n").encode())
        return json.loads(sock.makefile("r", encoding="utf-8").readline())

deadline = time.time() + 120
pending = set(range(NODE_COUNT))
while pending and time.time() < deadline:
    for node_id in list(pending):
        try:
            result = request(f"localhost", {"type": "PING"}, timeout=0.2) if False else None
        except Exception:
            pass
    # Host-side readiness is easier via mapped ports.
    for node_id in list(pending):
        host_port = 8001 + node_id
        try:
            with socket.create_connection(("127.0.0.1", host_port), timeout=0.5) as sock:
                sock.sendall((json.dumps({"type": "PING"}) + "\n").encode())
                line = sock.makefile("r", encoding="utf-8").readline()
                if json.loads(line).get("ok"):
                    pending.remove(node_id)
        except Exception:
            pass
    if pending:
        print("Waiting for nodes:", sorted(pending))
        time.sleep(2)

if pending:
    raise SystemExit(f"Cluster did not become ready: {sorted(pending)}")
print("All 10 nodes are reachable.")
