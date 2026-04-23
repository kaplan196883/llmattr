from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class BasinEntryResult:
    target_cluster: int
    entry_step: int | None       # None if the run never reaches the threshold
    late_fraction_in_target: float  # fraction of last (late_fraction) of steps in target
    reached: bool


def detect_basin_entry(
    labels: np.ndarray,
    steps: np.ndarray,
    target_cluster: int,
    fraction_after: float = 0.7,
) -> BasinEntryResult:
    """
    Earliest step index s such that the fraction of labels[s:] equal to
    target_cluster is >= fraction_after. Returns None if no such step exists.

    `fraction_after` defines what counts as "inside the basin": after entry,
    at least fraction_after of the remaining steps must stay in target.
    """
    if len(labels) == 0 or target_cluster < 0:
        return BasinEntryResult(
            target_cluster=int(target_cluster),
            entry_step=None,
            late_fraction_in_target=0.0,
            reached=False,
        )
    order = np.argsort(steps)
    labels_ord = labels[order]
    steps_ord = steps[order]

    n = len(labels_ord)
    match = (labels_ord == target_cluster).astype(np.int32)

    # suffix-sum: fraction_after_from[i] = match[i:].mean()
    # Compute once with cumsum.
    cum = np.cumsum(match[::-1])[::-1]
    remaining = np.arange(n, 0, -1)
    frac = cum / remaining  # shape (n,)

    hit = np.where(frac >= fraction_after)[0]
    if len(hit) == 0:
        return BasinEntryResult(
            target_cluster=int(target_cluster),
            entry_step=None,
            late_fraction_in_target=float(frac[-1]) if n else 0.0,
            reached=False,
        )
    i = int(hit[0])
    entry_step = int(steps_ord[i])
    return BasinEntryResult(
        target_cluster=int(target_cluster),
        entry_step=entry_step,
        late_fraction_in_target=float(frac[i]),
        reached=True,
    )
