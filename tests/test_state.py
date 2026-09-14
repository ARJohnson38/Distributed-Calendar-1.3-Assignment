import threading
from app.models import CalendarEvent
from app.state import NodeState

def make_event(node=0, num=1, start="13:00", end="13:20"):
    return CalendarEvent(
        event_id=f"N{node:02d}-E{num:02d}",
        creator_node=node,
        event_number=num,
        title=f"Node {node} Event {num}",
        simulation_date="2030-10-01",
        start_time=start,
        end_time=end,
        lamport_timestamp=1,
        vector_timestamp=[1 if i == node else 0 for i in range(10)],
    )

def test_local_and_send_increments():
    s = NodeState(0)
    l, v = s.local_event_tick()
    assert l == 1 and v[0] == 1
    l, v = s.send_tick()
    assert l == 2 and v[0] == 2

def test_vector_receive_merge():
    s = NodeState(4)
    before_l, before_v, after_l, after_v = s.receive_tick(
        34, [2,4,1,10,0,3,1,0,2,1]
    )
    assert after_l == 35
    assert after_v == [2,4,1,10,1,3,1,0,2,1]

def test_new_and_duplicate_merge_and_immutable_timestamp():
    s = NodeState(0)
    e = make_event()
    new, dup, conflicts = s.merge_events([e.to_dict()])
    assert (new, dup, conflicts) == (1,0,[])
    original = s.calendar[e.event_id].to_dict()
    new, dup, conflicts = s.merge_events([e.to_dict()])
    assert (new, dup, conflicts) == (0,1,[])
    assert s.calendar[e.event_id].to_dict() == original

def test_hash_independent_of_insertion_order():
    a = NodeState(0)
    b = NodeState(0)
    events = [make_event(0,1), make_event(1,1,"13:20","13:40")]
    a.merge_events([events[0].to_dict(), events[1].to_dict()])
    b.merge_events([events[1].to_dict(), events[0].to_dict()])
    assert a.canonical_hash() == b.canonical_hash()

def test_thread_safe_concurrent_merge():
    s = NodeState(0)
    events = [make_event(i % 10, i+1, "13:00", "13:20").to_dict() for i in range(10)]
    threads = [threading.Thread(target=s.merge_events, args=([e],)) for e in events]
    for t in threads: t.start()
    for t in threads: t.join()
    assert len(s.calendar) == 10
