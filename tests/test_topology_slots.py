from app.config import neighbor_ids
from app.scheduler import all_slots, choose_slots

def test_all_neighbors():
    expected = {
        0:(9,1), 1:(0,2), 2:(1,3), 3:(2,4), 4:(3,5),
        5:(4,6), 6:(5,7), 7:(6,8), 8:(7,9), 9:(8,0),
    }
    for node_id, pair in expected.items():
        assert neighbor_ids(node_id) == pair

def test_slots_are_30_and_twenty_minutes():
    slots = all_slots()
    assert len(slots) == 30
    assert slots[0] == ("13:00", "13:20")
    assert slots[-1] == ("22:40", "23:00")

def test_choose_ten_distinct_slots():
    slots = choose_slots(123)
    assert len(slots) == 10
    assert len(set(slots)) == 10
