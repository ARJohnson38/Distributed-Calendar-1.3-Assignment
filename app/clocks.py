from enum import Enum

class VectorRelation(str, Enum):
    BEFORE = "BEFORE"
    AFTER = "AFTER"
    EQUAL = "EQUAL"
    CONCURRENT = "CONCURRENT"

def lamport_receive(local_value: int, received_value: int) -> int:
    return max(local_value, received_value) + 1

def compare_vectors(a: list[int], b: list[int]) -> VectorRelation:
    if a == b:
        return VectorRelation.EQUAL

    a_le_b = all(x <= y for x, y in zip(a, b))
    b_le_a = all(y <= x for x, y in zip(a, b))

    if a_le_b and any(x < y for x, y in zip(a, b)):
        return VectorRelation.BEFORE
    if b_le_a and any(y < x for x, y in zip(a, b)):
        return VectorRelation.AFTER
    return VectorRelation.CONCURRENT
