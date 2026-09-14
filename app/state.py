from __future__ import annotations
import hashlib
import json
import threading
from copy import deepcopy
from typing import Iterable

from .clocks import lamport_receive
from .models import CalendarEvent

class NodeState:
    def __init__(self, node_id: int, node_count: int = 10):
        self.node_id = node_id
        self.node_count = node_count
        self.lamport = 0
        self.vector = [0] * node_count
        self.calendar: dict[str, CalendarEvent] = {}
        self._lock = threading.RLock()

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "lamport": self.lamport,
                "vector": list(self.vector),
                "calendar": [event.to_dict() for event in self.calendar.values()],
                "calendar_size": len(self.calendar),
                "state_hash": self.canonical_hash(),
            }

    def local_event_tick(self) -> tuple[int, list[int]]:
        with self._lock:
            self.lamport += 1
            self.vector[self.node_id] += 1
            return self.lamport, list(self.vector)

    def send_tick(self) -> tuple[int, list[int]]:
        with self._lock:
            self.lamport += 1
            self.vector[self.node_id] += 1
            return self.lamport, list(self.vector)

    def receive_tick(self, received_lamport: int, received_vector: list[int]) -> tuple[int, list[int], int, list[int]]:
        with self._lock:
            lamport_before = self.lamport
            vector_before = list(self.vector)
            self.lamport = lamport_receive(self.lamport, received_lamport)
            self.vector = [max(a, b) for a, b in zip(self.vector, received_vector)]
            self.vector[self.node_id] += 1
            return lamport_before, vector_before, self.lamport, list(self.vector)

    def add_local_event(self, event: CalendarEvent) -> None:
        with self._lock:
            if event.event_id in self.calendar:
                raise ValueError(f"duplicate local event_id {event.event_id}")
            self.calendar[event.event_id] = event

    def merge_events(self, incoming: Iterable[dict]) -> tuple[int, int, list[str]]:
        new_events = 0
        duplicates = 0
        conflicts: list[str] = []
        with self._lock:
            for raw in incoming:
                event = CalendarEvent.from_dict(raw)
                existing = self.calendar.get(event.event_id)
                if existing is None:
                    self.calendar[event.event_id] = event
                    new_events += 1
                elif existing.to_dict() == event.to_dict():
                    duplicates += 1
                else:
                    conflicts.append(event.event_id)
        return new_events, duplicates, conflicts

    def calendar_copy(self) -> list[dict]:
        with self._lock:
            return [deepcopy(e.to_dict()) for e in self.calendar.values()]

    def canonical_hash(self) -> str:
        with self._lock:
            canonical = [
                self.calendar[event_id].to_dict()
                for event_id in sorted(self.calendar)
            ]
            payload = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
            return hashlib.sha256(payload).hexdigest()
