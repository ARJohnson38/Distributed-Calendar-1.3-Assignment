from app.clocks import lamport_receive, compare_vectors, VectorRelation

def test_lamport_receive_rule():
    assert lamport_receive(4, 9) == 10
    assert lamport_receive(12, 9) == 13

def test_vector_comparisons():
    assert compare_vectors([1,0,0], [1,0,0]) == VectorRelation.EQUAL
    assert compare_vectors([1,0,0], [2,0,0]) == VectorRelation.BEFORE
    assert compare_vectors([2,0,0], [1,0,0]) == VectorRelation.AFTER
    assert compare_vectors([1,0,0], [0,1,0]) == VectorRelation.CONCURRENT
