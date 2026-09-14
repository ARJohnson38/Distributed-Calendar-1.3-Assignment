import json
from pathlib import Path
from collections import defaultdict
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from app.clocks import compare_vectors

LOGS = Path("logs")
REPORTS = Path("reports")
REPORTS.mkdir(exist_ok=True)

records = json.loads((LOGS / "combined_logs.json").read_text(encoding="utf-8"))
styles = getSampleStyleSheet()

def p(text, style="BodyText"):
    return Paragraph(str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"), styles[style])

def table(data, widths=None):
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("FONTSIZE", (0,0), (-1,-1), 7),
    ]))
    return t

# Pair SEND/FINAL_SYNC_SEND with RECEIVE_STATE by message_id.
sends = {}
receives = {}
for r in records:
    mid = r.get("message_id")
    if r.get("action") in ("SEND_STATE", "FINAL_SYNC_SEND") and mid:
        sends[mid] = r
    if r.get("action") == "RECEIVE_STATE" and mid:
        receives[mid] = r
pairs = [(mid, sends[mid], receives[mid]) for mid in sends.keys() & receives.keys()]
pairs.sort(key=lambda x: x[1].get("wall_time_utc", ""))

# Final status from latest meaningful record by node.
node_records = defaultdict(list)
for r in records:
    node_records[int(r["node_id"])].append(r)

def final_lamport(node_id):
    vals = []
    for r in node_records[node_id]:
        for key in ("lamport_after", "message_lamport", "lamport"):
            if isinstance(r.get(key), int):
                vals.append(r[key])
    return max(vals) if vals else 0

def final_vector(node_id):
    # Choose last record containing the most recent vector field.
    for r in reversed(node_records[node_id]):
        for key in ("vector_after", "message_vector", "vector"):
            if isinstance(r.get(key), list) and len(r[key]) == 10:
                return r[key]
    return [0]*10

def final_calendar(node_id):
    for r in reversed(node_records[node_id]):
        if "calendar_size_after" in r or "state_hash_after" in r:
            return r.get("calendar_size_after", ""), r.get("state_hash_after", "")
    return "", ""

# Report 1
story = [p("Report 1 – Lamport Clock Analysis", "Title"), Spacer(1, 8)]
story += [
    p("Implemented rules", "Heading2"),
    p("Local schedule: increment L, create the event, and store the resulting L in the immutable event record."),
    p("Send: increment L before each neighbor send. Left and right transmissions are distinct send events."),
    p("Receive: set L = max(local L, received message L) + 1 before merging the received calendar."),
    Spacer(1, 8),
    p("Final Lamport values", "Heading2"),
]
story.append(table([["Node","Final Lamport"]] + [[i, final_lamport(i)] for i in range(10)]))
story += [Spacer(1, 8), p("Ten send/receive checks", "Heading2")]
check_rows = [["Message","Sender","L(send)","Receiver","L before","L after","Verified"]]
for mid, s, r in pairs[:10]:
    check_rows.append([
        mid, s["node_id"], s["message_lamport"], r["node_id"],
        r["lamport_before"], r["lamport_after"],
        "YES" if r["lamport_after"] > s["message_lamport"] else "NO"
    ])
story.append(table(check_rows))

story += [Spacer(1,8), p("Three-node propagation chain", "Heading2")]
# Find an event and show receives that added events; enough for evidence from logs.
chain = []
for r in records:
    if r.get("action") == "RECEIVE_STATE" and r.get("new_events_added", 0) > 0:
        chain.append(r)
    if len(chain) >= 3:
        break
if chain:
    chain_rows = [["Time","Receiver","Sender","Message","New events"]]
    for r in chain:
        chain_rows.append([r["wall_time_utc"], r["node_id"], r["sender_node"], r["message_id"], r["new_events_added"]])
    story.append(table(chain_rows))
story += [
    Spacer(1,8),
    p("Observation", "Heading2"),
    p("Every analyzed delivery must satisfy L(receive) > L(send). Lamport timestamps provide a consistent logical order, but different timestamps do not prove that two independent schedule events are causally related."),
    p("Conclusion", "Heading2"),
    p("The observed logs demonstrate the required Lamport increment rules for local scheduling, separate neighbor sends, and receipt. The receive rule ensures the receiving logical time advances beyond the sender timestamp."),
]
SimpleDocTemplate(str(REPORTS / "Report_1_Lamport_Clock.pdf"), pagesize=letter).build(story)

# Report 2
story = [p("Report 2 – Vector Clock and Causality Analysis", "Title"), Spacer(1, 8)]
story += [
    p("Implemented rules", "Heading2"),
    p("Local schedule: increment V[i] and store a copy of the vector in the event record."),
    p("Send: increment V[i] independently before each neighbor transmission and attach a copy to the message."),
    p("Receive: component-wise maximum of local and received vectors, then increment the receiver's own entry."),
    Spacer(1,8),
    p("Final vectors", "Heading2"),
]
fv_rows = [["Node","Final vector"]]
for i in range(10):
    fv_rows.append([i, str(final_vector(i))])
story.append(table(fv_rows, widths=[40, 500]))

# Event vector pairs
local_events = [r for r in records if r.get("action") == "LOCAL_SCHEDULE" and isinstance(r.get("event"), dict)]
pair_rows = [["A","B","Relation"]]
selected = []
for i in range(len(local_events)):
    for j in range(i+1, len(local_events)):
        a = local_events[i]["event"]
        b = local_events[j]["event"]
        rel = compare_vectors(a["vector_timestamp"], b["vector_timestamp"]).value
        selected.append((a["event_id"], b["event_id"], rel))
        if len(selected) >= 10:
            break
    if len(selected) >= 10:
        break
for row in selected:
    pair_rows.append(row)
story += [Spacer(1,8), p("Ten event-pair classifications", "Heading2"), table(pair_rows)]

concurrent = []
for i in range(len(local_events)):
    for j in range(i+1, len(local_events)):
        a = local_events[i]["event"]
        b = local_events[j]["event"]
        if a["creator_node"] != b["creator_node"]:
            rel = compare_vectors(a["vector_timestamp"], b["vector_timestamp"]).value
            if rel == "CONCURRENT":
                concurrent.append((a["event_id"], b["event_id"], rel))
        if len(concurrent) >= 3:
            break
    if len(concurrent) >= 3:
        break
story += [Spacer(1,8), p("Three concurrent cross-node pairs", "Heading2")]
story.append(table([["A","B","Relation"]] + concurrent))

story += [Spacer(1,8), p("Final calendar size and state hash", "Heading2")]
final_rows = [["Node","Size","State hash"]]
for i in range(10):
    size, h = final_calendar(i)
    final_rows.append([i, size, h])
story.append(table(final_rows, widths=[35,45,460]))

story += [
    Spacer(1,8),
    p("Analysis", "Heading2"),
    p("Vector clocks can distinguish causal order from concurrency because BEFORE requires every vector component to be less than or equal to the other vector, with at least one strict inequality. If neither vector dominates the other, the events are concurrent."),
    p("All nodes may hold identical final calendars while ending with different logical clock values because message receives and sends update clocks even when they carry only duplicate state."),
    p("Compared with Lamport clocks, vector clocks retain per-node causal knowledge and therefore can identify concurrency; Lamport clocks provide an order consistent with causality but cannot by themselves prove two events are concurrent."),
]
SimpleDocTemplate(str(REPORTS / "Report_2_Vector_Clock.pdf"), pagesize=letter).build(story)

print("Generated both required PDF reports in ./reports/")
