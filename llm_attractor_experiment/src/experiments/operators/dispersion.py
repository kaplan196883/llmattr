"""
Dispersion and global-drift metrics for detecting the exploratory regime.

Signatures:
- contractive  → dispersion shrinks or stabilizes; global drift bounded
- oscillatory  → dispersion bounded, oscillates
- exploratory  → dispersion grows monotonically; global drift grows without bound
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.spatial.distance import cdist


@dataclass
class DispersionStats:
    initial_dispersion: float       # std-of-distances for first half
    final_dispersion: float         # std-of-distances for second half
    dispersion_growth: float        # final - initial (>0 = expanding, <0 = contracting)
    global_drift_start: float       # distance from start to mid
    global_drift_end: float         # distance from start to end
    drift_monotonicity: float       # fraction of steps where distance-from-start increases
    n_points: int


def _dispersion(points: np.ndarray, metric: str) -> float:
    """Spread of a point set: mean pairwise distance."""
    if len(points) < 2:
        return 0.0
    # efficient: use mean of upper-triangle pairwise distances
    D = cdist(points, points, metric=metric)
    iu = np.triu_indices(len(points), k=1)
    return float(D[iu].mean())


def trajectory_dispersion(
    points: np.ndarray,
    metric: str = "cosine",
) -> DispersionStats:
    n = len(points)
    if n < 4:
        return DispersionStats(
            initial_dispersion=0.0,
            final_dispersion=0.0,
            dispersion_growth=0.0,
            global_drift_start=0.0,
            global_drift_end=0.0,
            drift_monotonicity=0.0,
            n_points=n,
        )

    mid = n // 2
    first_half_disp = _dispersion(points[:mid], metric)
    second_half_disp = _dispersion(points[mid:], metric)
    dispersion_growth = second_half_disp - first_half_disp

    # Distance from starting point to each subsequent point.
    x0 = points[0:1]
    d_from_start = cdist(x0, points, metric=metric).ravel()
    drift_start = float(d_from_start[mid])
    drift_end = float(d_from_start[-1])

    # Fraction of consecutive pairs where distance-from-start increases.
    increases = np.sum(np.diff(d_from_start) > 0)
    drift_monotonicity = float(increases / max(1, (n - 1)))

    return DispersionStats(
        initial_dispersion=first_half_disp,
        final_dispersion=second_half_disp,
        dispersion_growth=dispersion_growth,
        global_drift_start=drift_start,
        global_drift_end=drift_end,
        drift_monotonicity=drift_monotonicity,
        n_points=n,
    )
