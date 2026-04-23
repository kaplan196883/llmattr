from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class ExitReturnStats:
    target_cluster: int
    n_visits: int               # number of contiguous runs inside target_cluster
    n_exits: int                # exits FROM the target cluster (visits - 1 if still in it at end)
    n_returns: int              # exits followed by a later return
    return_probability: float   # n_returns / n_exits (0 if no exits)
    mean_time_to_return: float | None
    median_time_to_return: float | None
    total_time_in_target: int
    n_points_considered: int


def exit_return_for_trajectory(
    labels: np.ndarray,
    target_cluster: int,
    steps: np.ndarray | None = None,
    start_step: int | None = None,
) -> ExitReturnStats:
    """
    Count exits from target_cluster and re-entries, optionally restricted to
    steps >= start_step.

    An "exit" is a transition from label==target to label!=target.
    A "return" is a subsequent transition back to label==target.
    """
    n_all = len(labels)
    if n_all == 0 or target_cluster < 0:
        return ExitReturnStats(
            target_cluster=int(target_cluster),
            n_visits=0,
            n_exits=0,
            n_returns=0,
            return_probability=0.0,
            mean_time_to_return=None,
            median_time_to_return=None,
            total_time_in_target=0,
            n_points_considered=0,
        )

    if steps is None:
        steps_arr = np.arange(n_all)
    else:
        steps_arr = np.asarray(steps)

    order = np.argsort(steps_arr)
    labels_ord = labels[order]
    steps_ord = steps_arr[order]

    if start_step is not None:
        mask = steps_ord >= int(start_step)
        labels_ord = labels_ord[mask]
        steps_ord = steps_ord[mask]

    n = len(labels_ord)
    if n == 0:
        return ExitReturnStats(
            target_cluster=int(target_cluster),
            n_visits=0,
            n_exits=0,
            n_returns=0,
            return_probability=0.0,
            mean_time_to_return=None,
            median_time_to_return=None,
            total_time_in_target=0,
            n_points_considered=0,
        )

    in_target = (labels_ord == target_cluster).astype(np.int32)
    # Visit = contiguous run of in_target == 1
    # Find runs
    n_visits = 0
    prev = 0
    for v in in_target:
        if v == 1 and prev == 0:
            n_visits += 1
        prev = v

    # Exits: number of 1->0 transitions (not counting the "final exit" off the end)
    exits: list[int] = []  # indices in labels_ord where an exit starts (the 0)
    for i in range(1, n):
        if in_target[i - 1] == 1 and in_target[i] == 0:
            exits.append(i)

    # Returns: for each exit index i, look for next j > i with in_target[j] == 1
    times_to_return: list[int] = []
    for i in exits:
        later = np.where(in_target[i:] == 1)[0]
        if len(later) > 0:
            j = i + int(later[0])
            times_to_return.append(int(steps_ord[j] - steps_ord[i - 1]))
    n_exits = len(exits)
    n_returns = len(times_to_return)
    return_probability = (n_returns / n_exits) if n_exits > 0 else 0.0

    mean_t = float(np.mean(times_to_return)) if times_to_return else None
    med_t = float(np.median(times_to_return)) if times_to_return else None

    return ExitReturnStats(
        target_cluster=int(target_cluster),
        n_visits=n_visits,
        n_exits=n_exits,
        n_returns=n_returns,
        return_probability=return_probability,
        mean_time_to_return=mean_t,
        median_time_to_return=med_t,
        total_time_in_target=int(in_target.sum()),
        n_points_considered=n,
    )
