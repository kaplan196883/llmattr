from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


@dataclass
class WilsonCI:
    """Score-based binomial CI for a proportion p = k/n."""
    p: float       # observed proportion k / n
    lo: float      # lower bound
    hi: float      # upper bound
    k: int         # successes
    n: int         # trials
    confidence: float


def wilson_ci(k: int, n: int, confidence: float = 0.95) -> WilsonCI:
    """
    Wilson score interval for a binomial proportion.

    For switching-rate proportions in the perturbation pipeline (k =
    n_switched, n = n_total), this gives well-behaved CIs even for
    boundary cases (k=0 or k=n) where the normal approximation
    1.96·√(p(1-p)/n) collapses to a degenerate point. See ARTICLE.md
    §4.7 for the spec.

    Returns
    -------
    WilsonCI(p, lo, hi, k, n, confidence)
    """
    if n <= 0:
        return WilsonCI(p=float("nan"), lo=float("nan"), hi=float("nan"),
                        k=int(k), n=int(n), confidence=confidence)
    # Two-sided z-score for the requested confidence.
    alpha = 1.0 - confidence
    # inverse normal CDF for 1 - alpha/2 — use erfinv to avoid scipy dep
    z = math.sqrt(2.0) * _erfinv(1.0 - alpha)
    p_hat = k / n
    denom = 1.0 + z * z / n
    centre = (p_hat + z * z / (2 * n)) / denom
    half = (z / denom) * math.sqrt(p_hat * (1 - p_hat) / n + z * z / (4 * n * n))
    lo = max(0.0, centre - half)
    hi = min(1.0, centre + half)
    return WilsonCI(p=p_hat, lo=lo, hi=hi, k=int(k), n=int(n), confidence=confidence)


def _erfinv(x: float) -> float:
    """
    Inverse error function — used to convert a confidence level to a z-score
    without bringing in scipy. Implementation from Winitzki's approximation,
    accurate to <2e-3 across the whole [-1, 1] range, which is more than
    enough for confidence-interval z-scores.
    """
    if x <= -1.0:
        return -float("inf")
    if x >= 1.0:
        return float("inf")
    a = 0.147
    ln1mx2 = math.log(1.0 - x * x)
    term = 2.0 / (math.pi * a) + ln1mx2 / 2.0
    inner = term * term - ln1mx2 / a
    return math.copysign(math.sqrt(math.sqrt(inner) - term), x)


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
