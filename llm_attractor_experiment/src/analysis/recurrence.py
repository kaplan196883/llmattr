from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.spatial.distance import cdist


@dataclass
class RecurrenceStats:
    recurrence_count: int
    recurrence_rate: float
    avg_return_lag: float | None
    nearest_nonlocal_distance: float | None
    n_points: int


def _pairwise(points: np.ndarray, metric: str) -> np.ndarray:
    if metric == "cosine":
        return cdist(points, points, metric="cosine")
    if metric == "euclidean":
        return cdist(points, points, metric="euclidean")
    raise ValueError(f"unknown metric: {metric}")


def recurrence_for_trajectory(
    points: np.ndarray, epsilon: float, tau: int, metric: str = "cosine"
) -> RecurrenceStats:
    """
    Recurrence over a single trajectory with points z_0..z_{T-1}.
    Events: ||z_t - z_s|| < epsilon with |t - s| > tau.
    """
    n = len(points)
    if n < 2:
        return RecurrenceStats(0, 0.0, None, None, n)

    D = _pairwise(points, metric)
    # mask out local lags
    idx = np.arange(n)
    lag = np.abs(idx[:, None] - idx[None, :])
    nonlocal_mask = lag > tau
    # use only upper triangle to count each pair once
    upper = np.triu(nonlocal_mask, k=1)

    recur = (D < epsilon) & upper
    recurrence_count = int(np.sum(recur))
    total_nonlocal_pairs = int(np.sum(upper))
    recurrence_rate = (recurrence_count / total_nonlocal_pairs) if total_nonlocal_pairs > 0 else 0.0

    if recurrence_count > 0:
        lags = lag[recur]
        avg_return_lag = float(np.mean(lags))
    else:
        avg_return_lag = None

    # nearest nonlocal neighbor distance per point, averaged
    D_masked = np.where(nonlocal_mask, D, np.inf)
    np.fill_diagonal(D_masked, np.inf)
    if np.all(np.isinf(D_masked)):
        nnd = None
    else:
        nnd = float(np.mean(np.min(D_masked, axis=1)))

    return RecurrenceStats(
        recurrence_count=recurrence_count,
        recurrence_rate=recurrence_rate,
        avg_return_lag=avg_return_lag,
        nearest_nonlocal_distance=nnd,
        n_points=n,
    )


def recurrence_matrix(
    points: np.ndarray, epsilon: float, tau: int, metric: str = "cosine"
) -> np.ndarray:
    """Binary recurrence plot matrix (0/1) for visualization."""
    n = len(points)
    if n == 0:
        return np.zeros((0, 0), dtype=np.int8)
    D = _pairwise(points, metric)
    idx = np.arange(n)
    lag = np.abs(idx[:, None] - idx[None, :])
    mat = ((D < epsilon) & (lag > tau)).astype(np.int8)
    return mat
