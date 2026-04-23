from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.cluster import DBSCAN, KMeans


@dataclass
class ClusterResult:
    labels: np.ndarray  # (n,)
    method: str
    params: dict
    n_clusters: int
    n_noise: int


def cluster_points(points: np.ndarray, method: str, params: dict) -> ClusterResult:
    if method == "dbscan":
        eps = float(params.get("eps", 0.35))
        min_samples = int(params.get("min_samples", 4))
        model = DBSCAN(eps=eps, min_samples=min_samples, metric="euclidean")
        labels = model.fit_predict(points)
        n_clusters = int(len({l for l in labels if l != -1}))
        n_noise = int(np.sum(labels == -1))
        return ClusterResult(
            labels=labels.astype(np.int32),
            method="dbscan",
            params={"eps": eps, "min_samples": min_samples},
            n_clusters=n_clusters,
            n_noise=n_noise,
        )
    if method == "kmeans":
        k = int(params.get("n_clusters", 6))
        k = max(1, min(k, len(points)))
        model = KMeans(n_clusters=k, n_init=10, random_state=0)
        labels = model.fit_predict(points)
        return ClusterResult(
            labels=labels.astype(np.int32),
            method="kmeans",
            params={"n_clusters": k},
            n_clusters=k,
            n_noise=0,
        )
    raise ValueError(f"unknown clustering method: {method}")
