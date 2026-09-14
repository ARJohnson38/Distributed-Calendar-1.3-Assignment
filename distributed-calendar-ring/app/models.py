from __future__ import annotations
from dataclasses import dataclass, asdict
from copy import deepcopy

@dataclass(frozen=True)
class CalendarEvent:
    event_id: str
    creator_node: int
    event_number: int
    title: str
    simulation_date: str
    start_time: str
    end_time: str
    lamport_timestamp: int
    vector_timestamp: list[int]

    def to_dict(self) -> dict:
        return deepcopy(asdict(self))

    @classmethod
    def from_dict(cls, data: dict) -> "CalendarEvent":
        return cls(
            event_id=data["event_id"],
            creator_node=int(data["creator_node"]),
            event_number=int(data["event_number"]),
            title=data["title"],
            simulation_date=data["simulation_date"],
            start_time=data["start_time"],
            end_time=data["end_time"],
            lamport_timestamp=int(data["lamport_timestamp"]),
            vector_timestamp=list(data["vector_timestamp"]),
        )
