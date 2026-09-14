import json
import socket

NODE_COUNT = 10

def request_port(port: int, message: dict) -> dict:
    with socket.create_connection(("127.0.0.1", port), timeout=10) as sock:
        sock.sendall((json.dumps(message) + "\n").encode())
        return json.loads(sock.makefile("r", encoding="utf-8").readline())

rows = []
for node_id in range(NODE_COUNT):
    status = request_port(8001 + node_id, {"type": "STATUS"})
    rows.append(
        (
            node_id,
            status["calendar_size"],
            status["state_hash"],
            status["lamport"],
            status["vector"],
        )
    )

print("node,size,state_hash,lamport,vector")
for row in rows:
    print(f"{row[0]},{row[1]},{row[2]},{row[3]},\"{row[4]}\"")

sizes = {r[1] for r in rows}
hashes = {r[2] for r in rows}

if sizes == {100} and len(hashes) == 1:
    print("\nPASS: all ten nodes contain 100 events and have the same canonical state hash.")
else:
    print("\nFAIL: cluster has not converged.")
    raise SystemExit(1)
