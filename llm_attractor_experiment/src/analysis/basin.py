from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class BasinResult:
    prompt_family: str
    initial_condition_id: str
    target_cluster: int
    target_step: int
    n_runs: int
    n_converged: int
    basin_score: float  # n_converged / n_runs


def find_target_cluster(
    labels: np.ndarray,
    steps: np.ndarray,
    late_fraction: float,
) -> int:
    """
    Pick the most-visited non-noise cluster among late-time points
    (steps whose index >= (1 - late_fraction) * T).
    Returns -1 if no non-noise cluster exists.
    """
    if len(labels) == 0:
        return -1
    T = int(np.max(steps)) + 1
    cutoff = int(round((1.0 - late_fraction) * T))
    late_mask = steps >= cutoff
    late_labels = labels[late_mask]
    late_labels = late_labels[late_labels != -1]
    if len(late_labels) == 0:
        # fall back to global most common
        all_valid = labels[labels != -1]
        if len(all_valid) == 0:
            return -1
        vals, counts = np.unique(all_valid, return_counts=True)
        return int(vals[np.argmax(counts)])
    vals, counts = np.unique(late_labels, return_counts=True)
    return int(vals[np.argmax(counts)])


def basin_score_for_condition(
    labels_by_run: list[np.ndarray],
    steps_by_run: list[np.ndarray],
    target_cluster: int,
    target_step: int,
) -> tuple[int, int]:
    """
    Count how many runs visit target_cluster at any step >= target_step.
    Returns (n_converged, n_total).
    """
    n_converged = 0
    for labels, steps in zip(labels_by_run, steps_by_run):
        mask = steps >= target_step
        if np.any((labels[mask] == target_cluster)):
            n_converged += 1
    return n_converged, len(labels_by_run)
