# Step-by-Step Execution Guide

## Step 1 — Open the Project

```powershell
cd "C:\path\to\distributed-calendar-ring"
```

Confirm Docker Desktop is running.

## Step 2 — Run the Unit Tests

```powershell
python -m pytest -q
```

Capture the output for evidence.

## Step 3 — Build and Start All Ten Containers

```powershell
docker compose up --build -d
python scripts/wait_for_cluster.py
docker compose ps
```

Verify that node0 through node9 are all running.

## Step 4 — Verify the Ring Topology

Check Node 0:

```powershell
docker compose logs node0
```

The startup line should identify neighbors 9 and 1.

You may also check other nodes:

```powershell
docker compose logs node5
```

Node 5 should identify neighbors 4 and 6.

## Step 5 — Observe Event Creation and Neighbor Sends

Follow one node:

```powershell
docker compose logs -f node0
```

The actual structured evidence is stored in `/data/node-0.jsonl`.

Open another terminal and inspect it periodically:

```powershell
docker compose exec node0 tail -n 20 /data/node-0.jsonl
```

Look for:
- `LOCAL_SCHEDULE`
- `SEND_STATE`
- `RECEIVE_STATE`

## Step 6 — Wait for All Ten Schedulers to Finish

Do not manually stop the nodes. Each node must create exactly ten local events. Because the required delay is 30–90 seconds before every event, allow approximately 5–15 minutes.

## Step 7 — Run the Six Final Synchronization Rounds

```powershell
python scripts/run_final_sync.py
```

The script first waits until all schedulers report completion and then performs six rounds, one round at a time.

## Step 8 — Verify Final Convergence

```powershell
python scripts/verify_convergence.py
```

The required result is:
- every node has 100 unique events;
- all ten nodes have the same canonical calendar hash.

Save a screenshot of this result.

## Step 9 — Collect the Ten JSONL Logs

```powershell
python scripts/collect_logs.py
```

Confirm:

```powershell
dir logs
```

You should have `node-0.jsonl` through `node-9.jsonl`.

## Step 10 — Aggregate the Logs

```powershell
python scripts/aggregate_logs.py
```

Confirm:
- `logs/combined_logs.json`
- `logs/combined_logs.csv`

## Step 11 — Generate the Two Required Reports

```powershell
python scripts/generate_reports.py
```

Confirm:
- `reports/Report_1_Lamport_Clock.pdf`
- `reports/Report_2_Vector_Clock.pdf`

Open and review both reports before submission.

## Step 12 — Record the 5–8 Minute Demonstration

Show:
1. all ten containers healthy;
2. Node 0 neighbors 9 and 1;
3. a local 20-minute event;
4. its Lamport and vector timestamp;
5. full-calendar sends to both neighbors;
6. a neighbor receive and merge;
7. duplicate handling;
8. scheduler completion;
9. six final synchronization rounds;
10. final verification showing 100 events and one common state hash.

## Step 13 — Upload to GitHub

Upload the entire project, including source code, tests, logs, combined logs, reports, README, and any evidence screenshots.

## Step 14 — Final Submission

Submit the public GitHub URL and the narrated demonstration link required by your course.
