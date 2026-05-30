from pagination import paginate


def test_even_split():
    assert paginate([1, 2, 3, 4, 5, 6], 3) == [[1, 2, 3], [4, 5, 6]]


def test_last_partial_page_included():
    assert paginate(list(range(1, 11)), 3) == [
        [1, 2, 3], [4, 5, 6], [7, 8, 9], [10],
    ]


def test_single_page():
    assert paginate([1, 2], 5) == [[1, 2]]


def test_exact_multiple():
    assert paginate([1, 2, 3, 4], 2) == [[1, 2], [3, 4]]
