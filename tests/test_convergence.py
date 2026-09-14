from app.models import CalendarEvent
from app.state import NodeState

def event(node, num):
    return CalendarEvent(
        event_id=f"N{node:02d}-E{num:02d}",
        creator_node=node,
        event_number=num,
        title=f"Node {node} Event {num}",
        simulation_date="2030-10-01",
        start_time="13:00",
        end_time="13:20",
        lamport_timestamp=num,
        vector_timestamp=[num if i == node else 0 for i in range(10)],
    ).to_dict()

def test_ten_node_ring_converges_with_six_rounds():
    states = [NodeState(i) for i in range(10)]
    for i, st in enumerate(states):
        st.merge_events([event(i, n) for n in range(1, 11)])

    for _ in range(6):
        snapshots = [s.calendar_copy() for s in states]
        for i in range(10):
            left = (i - 1) % 10
            right = (i + 1) % 10
            states[left].merge_events(snapshots[i])
            states[right].merge_events(snapshots[i])

    assert all(len(s.calendar) == 100 for s in states)
    hashes = {s.canonical_hash() for s in states}
    assert len(hashes) == 1
