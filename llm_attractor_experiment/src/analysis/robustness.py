from __future__ import annotations

import numpy as np
import pandas as pd


def time_shuffle_labels(labels: np.ndarray, rng: np.random.Generator | None = None) -> np.ndarray:
    """Shuffle a 1D sequence of cluster labels in place-safe way for the time-shuffled baseline."""
    rng = rng or np.random.default_rng(0)
    idx = np.arange(len(labels))
    rng.shuffle(idx)
    return labels[idx]


def summarize_metric(df: pd.DataFrame, value_col: str, group_cols: list[str]) -> pd.DataFrame:
    """mean, std, n per group."""
    if df.empty:
        return pd.DataFrame(columns=group_cols + [f"{value_col}_mean", f"{value_col}_std", "n"])
    agg = df.groupby(group_cols, dropna=False)[value_col].agg(["mean", "std", "count"]).reset_index()
    agg = agg.rename(
        columns={"mean": f"{value_col}_mean", "std": f"{value_col}_std", "count": "n"}
    )
    return agg


def effect_vs_baseline(
    main_df: pd.DataFrame,
    baseline_df: pd.DataFrame,
    value_col: str,
    group_cols: list[str],
) -> pd.DataFrame:
    """
    Per group, mean(main) - mean(baseline) and normalized effect size
    (mean_diff / pooled_std). Returns one row per group present in either side.
    """
    main = summarize_metric(main_df, value_col, group_cols)
    base = summarize_metric(baseline_df, value_col, group_cols)
    if main.empty and base.empty:
        return pd.DataFrame()
    merged = pd.merge(
        main,
        base,
        how="outer",
        on=group_cols,
        suffixes=("_main", "_base"),
    )
    mean_m = merged.get(f"{value_col}_mean_main")
    mean_b = merged.get(f"{value_col}_mean_base")
    std_m = merged.get(f"{value_col}_std_main").fillna(0)
    std_b = merged.get(f"{value_col}_std_base").fillna(0)
    diff = mean_m - mean_b
    pooled = np.sqrt((std_m**2 + std_b**2) / 2.0).replace(0, np.nan)
    merged["mean_diff"] = diff
    merged["effect_size"] = diff / pooled
    merged["sign"] = np.sign(diff).fillna(0).astype(int)
    return merged
