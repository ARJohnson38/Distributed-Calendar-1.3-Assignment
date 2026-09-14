# Distributed Calendar on a Ten-Node Docker Ring

Advanced Operating Systems programming assignment implementing a ten-node Docker ring with Lamport clocks, ten-entry vector clocks, immutable calendar-event records, full-state exchange, final synchronization, and log analysis.

## Architecture

Each node has exactly two neighbors:

| Node | Left | Right |
|---:|---:|---:|
| 0 | 9 | 1 |
| 1 | 0 | 2 |
| 2 | 1 | 3 |
| 3 | 2 | 4 |
| 4 | 3 | 5 |
| 5 | 4 | 6 |
| 6 | 5 | 7 |
| 7 | 6 | 8 |
| 8 | 7 | 9 |
| 9 | 8 | 0 |

Each node:
- listens on internal TCP port 8000;
- receives NODE_ID through an environment variable;
- has its own persistent Docker volume;
- creates exactly 10 distinct 20-minute events after random 30–90 second delays;
- sends its complete calendar to the left and right neighbor after each local event;
- keeps a Lamport clock, 10-entry vector clock, replicated calendar, and JSONL log.

## Start the Cluster

```powershell
docker compose up --build -d
python scripts/wait_for_cluster.py
docker compose ps
```

The scheduler begins automatically after the service starts. A normal run can take roughly 5–15 minutes because every node waits 30–90 seconds before each of its 10 local events.

## Watch Logs

```powershell
docker compose logs -f node0
```

You can also inspect one node's persisted JSONL file:

```powershell
docker compose exec node0 cat /data/node-0.jsonl
```

## Run Automated Tests

```powershell
python -m pytest -q
```

## Run Final Synchronization

After all ten schedulers have completed:

```powershell
python scripts/run_final_sync.py
```

This script waits until all ten nodes report scheduler completion and then runs six final synchronization rounds.

## Verify Convergence

```powershell
python scripts/verify_convergence.py
```

Expected result:

```text
PASS: all ten nodes contain 100 events and have the same canonical state hash.
```

## Collect and Aggregate Logs

```powershell
python scripts/collect_logs.py
python scripts/aggregate_logs.py
```

This creates:
- `logs/node-0.jsonl` through `logs/node-9.jsonl`
- `logs/combined_logs.json`
- `logs/combined_logs.csv`

## Generate the Required PDF Reports

```powershell
python scripts/generate_reports.py
```

This generates:
- `reports/Report_1_Lamport_Clock.pdf`
- `reports/Report_2_Vector_Clock.pdf`

Review both reports before submission to make sure the examples selected from the logs are clear and representative.

## Stop the Cluster

```powershell
docker compose down
```

To remove the ten persistent node volumes too:

```powershell
docker compose down -v
```

## Submission Checklist

- Public GitHub repository
- Source code
- Dockerfile and docker-compose.yml
- Automated tests and test output
- Ten JSONL node logs
- Combined CSV or JSON log file
- Report_1_Lamport_Clock.pdf
- Report_2_Vector_Clock.pdf
- README
- 5–8 minute narrated demonstration

## Video Demonstration

A 5–8 minute demonstration of the Distributed Calendar on a Ten-Node Docker Ring is available below.

[Watch the Distributed Calendar Demonstration Video] https://1drv.ms/v/c/74837dc9b967c4d3/IQDiHgGMaWd9SJQGnWbTTwmhAX9SPTarZ2LTearUk3S3aK8?e=beEvlF
