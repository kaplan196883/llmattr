from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class DwellStats:
    cluster: int
    mean_dwell: float
    median_dwell: float
    longest_dwell: int
    reentry_count: int
    total_visits: int
    occupancy: float  # fraction of steps spent in cluster


def dwell_runs(labels: np.ndarray) -> list[tuple[int, int, int]]:
    """Return list of (cluster_label, start_idx, length) contiguous runs."""
    if len(labels) == 0:
        return []
    runs: list[tuple[int, int, int]] = []
    start = 0
    cur = labels[0]
    for i in range(1, len(labels)):
        if labels[i] != cur:
            runs.append((int(cur), start, i - start))
            start = i
            cur = labels[i]
    runs.append((int(cur), start, len(labels) - start))
    return runs


def dwell_stats_for_trajectory(labels: np.ndarray) -> list[DwellStats]:
    """
    Per-cluster dwell statistics for a single trajectory's cluster-label sequence.
    Skips the DBSCAN noise label (-1).
    """
    runs = dwell_runs(labels)
    by_cluster: dict[int, list[int]] = {}
    for cid, _start, length in runs:
        if cid == -1:
            continue
        by_cluster.setdefault(cid, []).append(length)

    n = len(labels)
    stats: list[DwellStats] = []
    for cid, lengths in by_cluster.items():
        arr = np.array(lengths, dtype=np.int32)
        reentries = max(0, len(arr) - 1)
        total_visits = int(np.sum(arr))
        stats.append(
            DwellStats(
                cluster=cid,
                mean_dwell=float(arr.mean()),
                median_dwell=float(np.median(arr)),
                longest_dwell=int(arr.max()),
                reentry_count=reentries,
                total_visits=total_visits,
                occupancy=total_visits / n if n else 0.0,
            )
        )
    stats.sort(key=lambda s: s.cluster)
    return stats
