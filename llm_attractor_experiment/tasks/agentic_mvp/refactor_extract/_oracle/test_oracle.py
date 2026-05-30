import pytest

from service import fetch_user, fetch_order, TransientError


class FlakyClient:
    def __init__(self, fail_times):
        self.fail_times = fail_times
        self.user_calls = 0
        self.order_calls = 0

    def get_user(self, user_id):
        self.user_calls += 1
        if self.user_calls <= self.fail_times:
            raise TransientError()
        return f"user:{user_id}"

    def get_order(self, order_id):
        self.order_calls += 1
        if self.order_calls <= self.fail_times:
            raise TransientError()
        return f"order:{order_id}"


def test_user_retries_then_succeeds():
    assert fetch_user(FlakyClient(2), 7) == "user:7"


def test_order_retries_then_succeeds():
    assert fetch_order(FlakyClient(2), 9) == "order:9"


def test_user_gives_up_after_max():
    with pytest.raises(TransientError):
        fetch_user(FlakyClient(5), 1, max_attempts=3)


def test_order_gives_up_after_max():
    with pytest.raises(TransientError):
        fetch_order(FlakyClient(5), 1, max_attempts=3)
