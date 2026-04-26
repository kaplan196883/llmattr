"""
Pairwise-distance helpers shared across analysis modules.

Centralizes the small utilities that recurrence/periodicity/lyapunov each
used to define locally:

  - pairwise_distances(points, metric) -> square distance matrix
  - pairwise_mean_distance(points)     -> scalar mean upper-triangle distance
"""
from __future__ import annotations

import numpy as np
from scipy.spatial.distance import pdist, squareform


def pairwise_distances(points: np.ndarray, metric: str = "cosine") -> np.ndarray:
    """Square symmetric distance matrix using scipy.spatial.distance.pdist.

    Faster than cdist(points, points, ...) because it only computes the upper
    triangle; the result is reflected via squareform.
    """
    return squareform(pdist(points, metric=metric))


def pairwise_mean_distance(points: np.ndarray) -> float:
    """Mean Euclidean distance between distinct point pairs (upper triangle).

    Returns 0.0 for fewer than 2 points.
    """
    if len(points) < 2:
        return 0.0
    diff = points[:, None, :] - points[None, :, :]
    dists = np.linalg.norm(diff, axis=-1)
    iu = np.triu_indices(len(points), k=1)
    return float(dists[iu].mean())
