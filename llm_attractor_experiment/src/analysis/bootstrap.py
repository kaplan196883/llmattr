from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class BootstrapCI:
    mean: float
    lo: float
    hi: float
    n: int
    n_resamples: int
    confidence: float


def bootstrap_mean_ci(
    values: np.ndarray,
    n_resamples: int = 1000,
    confidence: float = 0.95,
    seed: int = 0,
) -> BootstrapCI:
    """
    Simple nonparametric bootstrap CI for the mean of `values`.
    """
    arr = np.asarray(values, dtype=np.float64)
    arr = arr[~np.isnan(arr)]
    n = len(arr)
    if n == 0:
        return BootstrapCI(
            mean=float("nan"),
            lo=float("nan"),
            hi=float("nan"),
            n=0,
            n_resamples=n_resamples,
            confidence=confidence,
        )
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(n_resamples, n))
    means = arr[idx].mean(axis=1)
    alpha = 1.0 - confidence
    lo = float(np.quantile(means, alpha / 2.0))
    hi = float(np.quantile(means, 1.0 - alpha / 2.0))
    return BootstrapCI(
        mean=float(arr.mean()),
        lo=lo,
        hi=hi,
        n=n,
        n_resamples=n_resamples,
        confidence=confidence,
    )


def permutation_test_mean_diff(
    a: np.ndarray,
    b: np.ndarray,
    n_resamples: int = 2000,
    seed: int = 0,
) -> dict:
    """
    Two-sided permutation test for the difference of means between `a` and `b`.
    Returns observed mean_diff and a two-sided p-value.
    """
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    a = a[~np.isnan(a)]
    b = b[~np.isnan(b)]
    na, nb = len(a), len(b)
    if na == 0 or nb == 0:
        return {"mean_diff": float("nan"), "p_value": float("nan"), "n_a": na, "n_b": nb}

    observed = float(a.mean() - b.mean())
    combined = np.concatenate([a, b])
    rng = np.random.default_rng(seed)
    count = 0
    for _ in range(n_resamples):
        rng.shuffle(combined)
        diff = combined[:na].mean() - combined[na:].mean()
        if abs(diff) >= abs(observed):
            count += 1
    p = count / n_resamples
    return {
        "mean_diff": observed,
        "p_value": float(p),
        "n_a": na,
        "n_b": nb,
        "n_resamples": n_resamples,
    }
