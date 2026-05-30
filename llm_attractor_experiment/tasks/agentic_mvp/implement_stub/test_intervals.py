from intervals import merge_intervals


def test_overlapping():
    assert merge_intervals([[1, 3], [2, 6], [8, 10]]) == [[1, 6], [8, 10]]


def test_touching_merges():
    assert merge_intervals([[1, 2], [2, 3]]) == [[1, 3]]
