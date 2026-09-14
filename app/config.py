import os
from dataclasses import dataclass

NODE_COUNT = 10
INTERNAL_PORT = 8000
SIMULATION_DATE = os.getenv("SIMULATION_DATE", "2030-10-01")
BASE_RANDOM_SEED = int(os.getenv("BASE_RANDOM_SEED", "47300"))
FINAL_SYNC_ROUNDS = int(os.getenv("FINAL_SYNC_ROUNDS", "6"))

def neighbor_ids(node_id: int) -> tuple[int, int]:
    return ((node_id - 1) % NODE_COUNT, (node_id + 1) % NODE_COUNT)

def node_host(node_id: int) -> str:
    return f"node{node_id}"

@dataclass(frozen=True)
class Settings:
    node_id: int
    port: int = INTERNAL_PORT
    simulation_date: str = SIMULATION_DATE
    base_seed: int = BASE_RANDOM_SEED

    @property
    def left_id(self) -> int:
        return neighbor_ids(self.node_id)[0]

    @property
    def right_id(self) -> int:
        return neighbor_ids(self.node_id)[1]

    @property
    def left_host(self) -> str:
        return node_host(self.left_id)

    @property
    def right_host(self) -> str:
        return node_host(self.right_id)

def load_settings() -> Settings:
    node_id = int(os.environ["NODE_ID"])
    if not 0 <= node_id < NODE_COUNT:
        raise ValueError("NODE_ID must be from 0 through 9")
    return Settings(node_id=node_id)
