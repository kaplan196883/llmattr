import time


def fetch_user(client, user_id, max_attempts=3):
    """Fetch a user, retrying on transient errors."""
    attempt = 0
    while True:
        try:
            return client.get_user(user_id)
        except TransientError:
            attempt += 1
            if attempt >= max_attempts:
                raise
            time.sleep(0.01 * attempt)


def fetch_order(client, order_id, max_attempts=3):
    """Fetch an order, retrying on transient errors."""
    attempt = 0
    while True:
        try:
            return client.get_order(order_id)
        except TransientError:
            attempt += 1
            if attempt >= max_attempts:
                raise
            time.sleep(0.01 * attempt)


class TransientError(Exception):
    pass
