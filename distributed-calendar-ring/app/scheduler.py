from __future__ import annotations
import random
import time
from datetime import datetime, timedelta

from .models import CalendarEvent

def all_slots() -> list[tuple[str, str]]:
    base = datetime.strptime("13:00", "%H:%M")
    slots = []
    for i in range(30):
        start = base + timedelta(minutes=20 * i)
        end = start + timedelta(minutes=20)
        slots.append((start.strftime("%H:%M"), end.strftime("%H:%M")))
    return slots

def choose_slots(seed: int, count: int = 10) -> list[tuple[str, str]]:
    rng = random.Random(seed)
    return rng.sample(all_slots(), count)

def scheduler_loop(node, sleep_fn=time.sleep) -> None:
    settings = node.settings
    slots = choose_slots(settings.base_seed + settings.node_id, 10)
    rng = random.Random(settings.base_seed + settings.node_id)

    for event_number, (start_time, end_time) in enumerate(slots, start=1):
        delay = rng.randint(30, 90)
        sleep_fn(delay)
        lamport_ts, vector_ts = node.state.local_event_tick()

        event = CalendarEvent(
            event_id=f"N{settings.node_id:02d}-E{event_number:02d}",
            creator_node=settings.node_id,
            event_number=event_number,
            title=f"Node {settings.node_id} Event {event_number}",
            simulation_date=settings.simulation_date,
            start_time=start_time,
            end_time=end_time,
            lamport_timestamp=lamport_ts,
            vector_timestamp=vector_ts,
        )
        node.state.add_local_event(event)
        node.logger.write(
            "LOCAL_SCHEDULE",
            event=event.to_dict(),
            lamport_after=lamport_ts,
            vector_after=vector_ts,
            calendar_size_after=len(node.state.calendar),
            state_hash_after=node.state.canonical_hash(),
            scheduled_delay_seconds=delay,
        )

        node.send_full_calendar(settings.left_id, final_sync=False)
        node.send_full_calendar(settings.right_id, final_sync=False)

    node.scheduler_complete.set()
    node.logger.write(
        "SCHEDULER_COMPLETE",
        lamport=node.state.lamport,
        vector=list(node.state.vector),
        calendar_size=len(node.state.calendar),
        state_hash=node.state.canonical_hash(),
    )
