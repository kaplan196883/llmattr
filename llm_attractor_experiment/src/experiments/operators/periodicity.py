"""
Periodicity and autocorrelation metrics for detecting oscillatory attractors
(2-cycles, k-cycles) in recursive LLM trajectories.

Primary target: distinguish the "oscillatory" regime (limit cycles) from the
"contractive" regime (fixed-point basins). Oscillatory signature: points at
lag k are closer in embedding space than points at lag 1.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.spatial.distance import pdist, squareform


@dataclass
class PeriodicityStats:
    period_2_score: float          # mean_dist(lag=1) - mean_dist(lag=2); >0 = 2-cycle evidence
    period_3_score: float          # similar for 3-cycle
    best_period: int | None        # lag with the smallest mean pairwise distance (1..T//2)
    best_period_dist: float        # mean pairwise distance at that lag
    autocorr_lags: list[int]       # list of lags examined
    autocorr_distances: list[float]  # mean pairwise distance per lag
    n_points: int


def _pairwise_dist(points: np.ndarray, metric: str) -> np.ndarray:
    return squareform(pdist(points, metric=metric))


def trajectory_periodicity(
    points: np.ndarray,
    metric: str = "cosine",
    max_lag: int | None = None,
) -> PeriodicityStats:
    """
    For a trajectory of n points, compute mean pairwise distance at each lag
    k = 1, 2, ..., max_lag. A 2-cycle shows up as dist(lag=2) < dist(lag=1).
    """
    n = len(points)
    if n < 4:
        return PeriodicityStats(
            period_2_score=0.0,
            period_3_score=0.0,
            best_period=None,
            best_period_dist=float("nan"),
            autocorr_lags=[],
            autocorr_distances=[],
            n_points=n,
        )
    D = _pairwise_dist(points, metric)
    if max_lag is None:
        max_lag = n // 2

    lags: list[int] = []
    dists: list[float] = []
    for k in range(1, max_lag + 1):
        vals = np.array([D[i, i + k] for i in range(n - k)])
        lags.append(k)
        dists.append(float(vals.mean()))

    arr = np.array(dists)
    best_idx = int(arr.argmin())
    best_period = lags[best_idx]
    best_dist = float(arr[best_idx])

    d1 = dists[0] if len(dists) >= 1 else 0.0
    d2 = dists[1] if len(dists) >= 2 else 0.0
    d3 = dists[2] if len(dists) >= 3 else 0.0

    return PeriodicityStats(
        period_2_score=float(d1 - d2),
        period_3_score=float(d1 - d3),
        best_period=best_period,
        best_period_dist=best_dist,
        autocorr_lags=lags,
        autocorr_distances=dists,
        n_points=n,
    )
