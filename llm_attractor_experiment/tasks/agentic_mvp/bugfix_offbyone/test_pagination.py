from pagination import paginate


def test_even_split():
    assert paginate([1, 2, 3, 4, 5, 6], 3) == [[1, 2, 3], [4, 5, 6]]


def test_last_partial_page_included():
    assert paginate([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 3) == [
        [1, 2, 3], [4, 5, 6], [7, 8, 9], [10],
    ]
