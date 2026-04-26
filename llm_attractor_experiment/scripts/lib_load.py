"""
Shared loaders for cross-experiment aggregator scripts.

Centralizes the "iterate experiment IDs, read CSV at known subpath, skip
missing files" pattern that aggregate_*.py scripts each implemented locally.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd


def read_experiment_csv(
    data_dir: Path,
    exp_id: str,
    subpath: str | tuple[str, ...],
) -> pd.DataFrame | None:
    """Read `data_dir / exp_id / subpath` as a CSV; return DataFrame or None.

    `subpath` can be a single string ("reports/perturbation/switching_summary.csv")
    or a tuple of path components (("reports", "perturbation", "switching_summary.csv")).

    Returns None when the file is missing — callers iterate experiment IDs
    and silently skip ones that haven't been analyzed yet.
    """
    if isinstance(subpath, str):
        csv = data_dir / exp_id / subpath
    else:
        csv = data_dir.joinpath(exp_id, *subpath)
    if not csv.exists():
        print(f"[warn] missing {csv}")
        return None
    return pd.read_csv(csv)
