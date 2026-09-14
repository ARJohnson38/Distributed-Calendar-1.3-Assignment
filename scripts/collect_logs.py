import subprocess
from pathlib import Path

logs = Path("logs")
logs.mkdir(exist_ok=True)

for node_id in range(10):
    target = logs / f"node-{node_id}.jsonl"
    cmd = [
        "docker", "compose", "cp",
        f"node{node_id}:/data/node-{node_id}.jsonl",
        str(target),
    ]
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)

print("Collected all ten node logs into ./logs/")
