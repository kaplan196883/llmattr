def add(a, b):
    return a + b


def subtract(a, b):
    # BUG: returns the wrong result.
    return a - b + 1


def multiply(a, b):
    return a * b
