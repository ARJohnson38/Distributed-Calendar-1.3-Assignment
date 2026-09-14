from __future__ import annotations
import json
import os
import socketserver
import threading

from .config import INTERNAL_PORT, load_settings, node_host
from .logging_utils import JsonlLogger
from .neighbor_client import send_request
from .scheduler import scheduler_loop
from .state import NodeState

class ThreadingTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

class RequestHandler(socketserver.StreamRequestHandler):
    def handle(self):
        raw = self.rfile.readline()
        if not raw:
            return
        try:
            message = json.loads(raw.decode("utf-8"))
            response = self.server.node.handle_message(message)
        except Exception as exc:
            response = {"ok": False, "error": str(exc)}
        self.wfile.write((json.dumps(response) + "\n").encode("utf-8"))

class CalendarNode:
    def __init__(self):
        self.settings = load_settings()
        self.state = NodeState(self.settings.node_id)
        self.scheduler_complete = threading.Event()
        self.logger = JsonlLogger(
            self.settings.node_id,
            f"/data/node-{self.settings.node_id}.jsonl",
        )
        self.message_seq = 0
        self.message_lock = threading.Lock()

    def next_message_id(self) -> str:
        with self.message_lock:
            self.message_seq += 1
            return f"N{self.settings.node_id:02d}-M{self.message_seq:04d}"

    def send_full_calendar(self, receiver_id: int, final_sync: bool) -> None:
        message_lamport, message_vector = self.state.send_tick()
        message_id = self.next_message_id()
        calendar = self.state.calendar_copy()
        action = "FINAL_SYNC_SEND" if final_sync else "SEND_STATE"

        message = {
            "type": "STATE",
            "message_id": message_id,
            "sender_node": self.settings.node_id,
            "receiver_node": receiver_id,
            "message_lamport": message_lamport,
            "message_vector": message_vector,
            "calendar": calendar,
            "final_sync": final_sync,
        }

        self.logger.write(
            action,
            receiver_node=receiver_id,
            message_id=message_id,
            message_lamport=message_lamport,
            message_vector=message_vector,
            calendar_size_sent=len(calendar),
            state_hash_sent=self.state.canonical_hash(),
        )

        try:
            response = send_request(node_host(receiver_id), INTERNAL_PORT, message)
            if not response.get("ok"):
                raise RuntimeError(response.get("error", "unknown peer error"))
        except Exception as exc:
            self.logger.write(
                "ERROR",
                error_type="SEND_FAILURE",
                receiver_node=receiver_id,
                message_id=message_id,
                detail=str(exc),
            )

    def receive_state(self, message: dict) -> dict:
        required = {
            "message_id", "sender_node", "receiver_node",
            "message_lamport", "message_vector", "calendar"
        }
        missing = required - message.keys()
        if missing:
            raise ValueError(f"missing fields: {sorted(missing)}")

        lamport_before, vector_before, lamport_after, vector_after = self.state.receive_tick(
            int(message["message_lamport"]),
            list(message["message_vector"]),
        )
        new_events, duplicates, conflicts = self.state.merge_events(message["calendar"])

        if conflicts:
            self.logger.write(
                "ERROR",
                error_type="INCONSISTENT_DUPLICATE",
                message_id=message["message_id"],
                conflicting_event_ids=conflicts,
            )

        self.logger.write(
            "RECEIVE_STATE",
            sender_node=int(message["sender_node"]),
            message_id=message["message_id"],
            lamport_before=lamport_before,
            received_lamport=int(message["message_lamport"]),
            lamport_after=lamport_after,
            vector_before=vector_before,
            received_vector=list(message["message_vector"]),
            vector_after=vector_after,
            received_event_count=len(message["calendar"]),
            new_events_added=new_events,
            duplicates_ignored=duplicates,
            calendar_size_after=len(self.state.calendar),
            state_hash_after=self.state.canonical_hash(),
            final_sync=bool(message.get("final_sync", False)),
        )
        return {"ok": True, "calendar_size": len(self.state.calendar)}

    def handle_message(self, message: dict) -> dict:
        msg_type = message.get("type")
        if msg_type == "STATE":
            return self.receive_state(message)
        if msg_type == "STATUS":
            snap = self.state.snapshot()
            return {
                "ok": True,
                "node_id": self.settings.node_id,
                "scheduler_complete": self.scheduler_complete.is_set(),
                **snap,
            }
        if msg_type == "FINAL_SYNC":
            round_number = int(message["round"])
            self.send_full_calendar(self.settings.left_id, final_sync=True)
            self.send_full_calendar(self.settings.right_id, final_sync=True)
            return {
                "ok": True,
                "node_id": self.settings.node_id,
                "round": round_number,
                "calendar_size": len(self.state.calendar),
                "state_hash": self.state.canonical_hash(),
            }
        if msg_type == "PING":
            return {"ok": True, "node_id": self.settings.node_id}
        raise ValueError(f"unknown message type {msg_type!r}")

    def run(self):
        server = ThreadingTCPServer(("0.0.0.0", INTERNAL_PORT), RequestHandler)
        server.node = self

        scheduler_thread = threading.Thread(
            target=scheduler_loop,
            args=(self,),
            daemon=True,
        )
        scheduler_thread.start()

        self.logger.write(
            "NODE_START",
            left_neighbor=self.settings.left_id,
            right_neighbor=self.settings.right_id,
            port=INTERNAL_PORT,
        )
        print(
            f"Node {self.settings.node_id} listening on 0.0.0.0:{INTERNAL_PORT}; "
            f"neighbors={self.settings.left_id},{self.settings.right_id}",
            flush=True,
        )
        server.serve_forever()

if __name__ == "__main__":
    CalendarNode().run()
