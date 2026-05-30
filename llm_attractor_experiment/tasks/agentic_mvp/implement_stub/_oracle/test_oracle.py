from intervals import merge_intervals


def test_overlapping():
    assert merge_intervals([[1, 3], [2, 6], [8, 10]]) == [[1, 6], [8, 10]]


def test_touching_merges():
    assert merge_intervals([[1, 2], [2, 3]]) == [[1, 3]]


def test_unsorted_input():
    assert merge_intervals([[8, 10], [1, 3], [2, 6]]) == [[1, 6], [8, 10]]


def test_single():
    assert merge_intervals([[4, 5]]) == [[4, 5]]


def test_fully_contained():
    assert merge_intervals([[1, 10], [3, 4]]) == [[1, 10]]
