import os
import random

import numpy as np


def set_global_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed % (2**32))
    os.environ["PYTHONHASHSEED"] = str(seed)


def derive_seed(base_seed: int, *parts: object) -> int:
    h = base_seed & 0xFFFFFFFF
    for p in parts:
        s = str(p)
        for ch in s:
            h = (h * 1315423911) ^ ord(ch)
            h &= 0xFFFFFFFF
    return int(h)
