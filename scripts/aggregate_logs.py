import csv
import json
from datetime import datetime
from pathlib import Path

logs_dir = Path("logs")
records = []
for path in sorted(logs_dir.glob("node-*.jsonl")):
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                record = json.loads(line)
                record["_source_file"] = path.name
                records.append(record)

records.sort(key=lambda r: r.get("wall_time_utc", ""))

out_json = logs_dir / "combined_logs.json"
out_json.write_text(json.dumps(records, indent=2), encoding="utf-8")

# Flatten nested values to JSON strings for CSV readability.
fieldnames = sorted({key for r in records for key in r})
with (logs_dir / "combined_logs.csv").open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for r in records:
        row = {}
        for key in fieldnames:
            value = r.get(key, "")
            if isinstance(value, (list, dict)):
                value = json.dumps(value, sort_keys=True)
            row[key] = value
        writer.writerow(row)

print(f"Wrote {len(records)} combined log records.")
