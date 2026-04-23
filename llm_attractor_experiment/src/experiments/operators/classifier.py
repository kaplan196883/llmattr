"""
Three-axis classifier for operator experiments: H1a (convergence),
H1b (recurrence/orbit), H1c (divergence). Each returns one of:
  not_supported / weak_support / moderate_support / strong_support.

Inputs: the metric dataframes produced by the enriched analyze phase
(see src/experiments/operators/analyze_ext.py).
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class ThreeAxisDecision:
    h1a_convergence: str
    h1b_recurrence: str
    h1c_divergence: str
    h1a_signals: dict[str, bool]
    h1b_signals: dict[str, bool]
    h1c_signals: dict[str, bool]
    h1a_reasons: list[str]
    h1b_reasons: list[str]
    h1c_reasons: list[str]


def _pos_effect(df: pd.DataFrame, value_col: str, greater: bool = True) -> bool:
    """recursive vs time_shuffled (or max of other regimes if no time_shuffled)."""
    if df is None or df.empty or "regime" not in df.columns or value_col not in df.columns:
        return False
    by_regime = df.groupby("regime")[value_col].mean(numeric_only=True)
    if "recursive" not in by_regime.index:
        return False
    rec = by_regime["recursive"]
    comparator = (
        by_regime["time_shuffled"]
        if "time_shuffled" in by_regime.index
        else by_regime.drop(index="recursive", errors="ignore").max()
        if len(by_regime) > 1
        else None
    )
    if comparator is None or pd.isna(comparator):
        return False
    return bool(rec > comparator) if greater else bool(rec < comparator)


def classify_three_axis(
    recurrence_df: pd.DataFrame,
    late_recurrence_df: pd.DataFrame,
    dwell_df: pd.DataFrame,
    basin_df: pd.DataFrame,
    periodicity_df: pd.DataFrame,
    dispersion_df: pd.DataFrame,
    observables: list[str],
) -> ThreeAxisDecision:
    # --- H1a convergence (same as before) ---
    basin_positive = bool(
        basin_df is not None
        and not basin_df.empty
        and basin_df["basin_score"].mean(numeric_only=True) > 0.7
    )
    dwell_positive = _pos_effect(dwell_df, "mean_dwell")
    h1a_signals = {"basin_positive": basin_positive, "dwell_above_null": dwell_positive}
    h1a_core = sum([basin_positive, dwell_positive])
    h1a = (
        "strong_support" if h1a_core == 2
        else "moderate_support" if h1a_core == 1
        else "not_supported"
    )
    h1a_reasons = [
        (f"basin mean = {basin_df['basin_score'].mean():.3f}"
         if basin_df is not None and not basin_df.empty
         else "no basin data"),
        f"dwell above null: {'yes' if dwell_positive else 'no'}",
    ]

    # --- H1b recurrence / oscillatory ---
    late_rec_positive = _pos_effect(late_recurrence_df, "recurrence_rate")
    # period-2: expect positive (lag-1 distance > lag-2 distance)
    period_2_positive = False
    best_non1_period_frac = 0.0
    if periodicity_df is not None and not periodicity_df.empty:
        rec = periodicity_df[periodicity_df.get("regime", "recursive") == "recursive"] \
            if "regime" in periodicity_df.columns else periodicity_df
        if not rec.empty:
            period_2_positive = bool(rec["period_2_score"].mean() > 0)
            if "best_period" in rec.columns:
                non1 = (rec["best_period"] > 1).sum()
                best_non1_period_frac = float(non1 / len(rec))
    h1b_signals = {
        "late_recurrence_above_null": late_rec_positive,
        "period_2_score_positive": period_2_positive,
        "best_period_is_nontrivial_majority": best_non1_period_frac > 0.5,
    }
    h1b_core = sum([late_rec_positive, period_2_positive, best_non1_period_frac > 0.5])
    h1b = (
        "strong_support" if h1b_core == 3
        else "moderate_support" if h1b_core == 2
        else "weak_support" if h1b_core == 1
        else "not_supported"
    )
    h1b_reasons = [
        f"late-time recurrence above null: {'yes' if late_rec_positive else 'no'}",
        f"mean period-2 score: "
        + (f"{periodicity_df[periodicity_df.get('regime','recursive')=='recursive']['period_2_score'].mean():.4f}"
           if periodicity_df is not None and not periodicity_df.empty
           else "n/a"),
        f"fraction of runs whose best period is >1: {best_non1_period_frac:.2f}",
    ]

    # --- H1c divergence ---
    dispersion_grows = False
    drift_growing = False
    if dispersion_df is not None and not dispersion_df.empty:
        rec = dispersion_df[dispersion_df.get("regime", "recursive") == "recursive"] \
            if "regime" in dispersion_df.columns else dispersion_df
        if not rec.empty and "dispersion_growth" in rec.columns:
            dispersion_grows = bool(rec["dispersion_growth"].mean() > 0)
        if not rec.empty and "drift_monotonicity" in rec.columns:
            drift_growing = bool(rec["drift_monotonicity"].mean() > 0.6)
    # Lack of basin is a divergence signal too:
    no_stable_basin = bool(
        basin_df is None or basin_df.empty
        or basin_df["basin_score"].mean(numeric_only=True) < 0.3
    )
    h1c_signals = {
        "dispersion_growing": dispersion_grows,
        "drift_monotonically_outward": drift_growing,
        "no_stable_basin": no_stable_basin,
    }
    h1c_core = sum([dispersion_grows, drift_growing, no_stable_basin])
    h1c = (
        "strong_support" if h1c_core == 3
        else "moderate_support" if h1c_core == 2
        else "weak_support" if h1c_core == 1
        else "not_supported"
    )
    h1c_reasons = [
        f"dispersion growth (second-half > first-half): {'yes' if dispersion_grows else 'no'}",
        f"drift monotonically outward: {'yes' if drift_growing else 'no'}",
        f"no stable basin: {'yes' if no_stable_basin else 'no'}",
    ]

    return ThreeAxisDecision(
        h1a_convergence=h1a,
        h1b_recurrence=h1b,
        h1c_divergence=h1c,
        h1a_signals=h1a_signals,
        h1b_signals=h1b_signals,
        h1c_signals=h1c_signals,
        h1a_reasons=h1a_reasons,
        h1b_reasons=h1b_reasons,
        h1c_reasons=h1c_reasons,
    )
