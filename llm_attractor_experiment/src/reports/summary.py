from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.config import Config
from src.utils.io import ensure_dir


@dataclass
class EvidenceDecision:
    label: str  # not_supported, weak, moderate, strong
    reasons: list[str]
    signals: dict[str, bool]


@dataclass
class TwoAxisDecision:
    h1a_convergence: str   # not_supported / weak / moderate / strong
    h1b_recurrence: str    # not_supported / weak / moderate / strong
    h1a_reasons: list[str]
    h1b_reasons: list[str]
    h1a_signals: dict[str, bool]
    h1b_signals: dict[str, bool]


def classify_evidence(
    recurrence_df: pd.DataFrame,
    dwell_df: pd.DataFrame,
    basin_df: pd.DataFrame,
    observables: list[str],
    pca_dims: list[int],
) -> EvidenceDecision:
    """
    Classify the four-level evidence label.

    Uses:
      - recurrence_rate higher on 'recursive' regime than any baseline regime
      - mean_dwell higher on 'recursive' than any baseline regime
      - basin_score positive and above baseline median if baseline basin exists
      - robustness: signals present in >= 2 observables and in >= 1 non-PCA-2 space
    """
    reasons: list[str] = []

    def pos_effect(df: pd.DataFrame, value_col: str) -> bool:
        """
        Prefer `time_shuffled` as the null if present (proper temporal-null baseline).
        Otherwise fall back to max of any other regime. `no_feedback` is a
        degenerate stationary-sampling baseline and is NOT a fair comparator for
        within-trajectory dynamical metrics (recurrence, dwell).
        """
        if df.empty or "regime" not in df.columns:
            return False
        by_regime = df.groupby("regime")[value_col].mean(numeric_only=True)
        if "recursive" not in by_regime.index:
            return False
        recursive_val = by_regime["recursive"]
        if "time_shuffled" in by_regime.index:
            return bool(recursive_val > by_regime["time_shuffled"])
        other = by_regime.drop(index="recursive", errors="ignore")
        if other.empty:
            return False
        return bool(recursive_val > other.max())

    def robust_across_obs(df: pd.DataFrame, value_col: str) -> int:
        if df.empty or "observable" not in df.columns:
            return 0
        count = 0
        for obs, sub in df.groupby("observable"):
            if pos_effect(sub, value_col):
                count += 1
        return count

    def robust_across_spaces(df: pd.DataFrame, value_col: str) -> bool:
        if df.empty or "space" not in df.columns:
            return False
        for space, sub in df.groupby("space"):
            if str(space) != "pca2" and pos_effect(sub, value_col):
                return True
        return False

    recurrence_pos = pos_effect(recurrence_df, "recurrence_rate")
    dwell_pos = pos_effect(dwell_df, "mean_dwell")
    basin_pos = bool(not basin_df.empty and basin_df["basin_score"].mean() > 0.5)

    n_obs_recurrence = robust_across_obs(recurrence_df, "recurrence_rate")
    n_obs_dwell = robust_across_obs(dwell_df, "mean_dwell")
    non_pca2_recurrence = robust_across_spaces(recurrence_df, "recurrence_rate")

    signals = {
        "recurrence_above_baseline": recurrence_pos,
        "dwell_above_baseline": dwell_pos,
        "basin_convergence_positive": basin_pos,
        "robust_across_two_observables": max(n_obs_recurrence, n_obs_dwell) >= 2,
        "robust_non_pca2_space": non_pca2_recurrence,
    }

    if recurrence_pos:
        reasons.append("recurrence rate above baselines")
    else:
        reasons.append("recurrence rate not above baselines")
    if dwell_pos:
        reasons.append("mean dwell above baselines")
    else:
        reasons.append("mean dwell not above baselines")
    if basin_pos:
        reasons.append("mean basin score > 0.5")
    else:
        reasons.append("mean basin score <= 0.5 or missing")
    reasons.append(
        f"recurrence positive in {n_obs_recurrence}/{len(observables)} observables, "
        f"dwell positive in {n_obs_dwell}/{len(observables)}"
    )
    reasons.append(
        f"non-PCA-2 recurrence effect: {'yes' if non_pca2_recurrence else 'no'}"
    )

    core_hits = sum([recurrence_pos, dwell_pos, basin_pos])
    robustness_ok = signals["robust_across_two_observables"] and signals["robust_non_pca2_space"]

    if core_hits == 3 and robustness_ok:
        label = "strong_support"
    elif core_hits >= 3:
        label = "moderate_support"
    elif core_hits == 2:
        label = "moderate_support" if robustness_ok else "weak_support"
    elif core_hits == 1:
        label = "weak_support"
    else:
        label = "not_supported"

    return EvidenceDecision(label=label, reasons=reasons, signals=signals)


def classify_two_axis(
    recurrence_df: pd.DataFrame,
    late_recurrence_df: pd.DataFrame,
    dwell_df: pd.DataFrame,
    basin_df: pd.DataFrame,
    exit_return_df: pd.DataFrame,
    observables: list[str],
) -> TwoAxisDecision:
    """
    H1a — convergence (basins + dwell)
    H1b — recurrence (late-time recurrence + exit/return)

    Rules:
      - time_shuffled is the preferred temporal null (via pos_effect).
      - non-PCA-2 / non-t-SNE-2 robustness is required for `strong`.
    """
    def pos_effect(df: pd.DataFrame, value_col: str, filter_kv: dict | None = None) -> bool:
        if df is None or df.empty or "regime" not in df.columns or value_col not in df.columns:
            return False
        if filter_kv:
            for k, v in filter_kv.items():
                if k in df.columns:
                    df = df[df[k] == v]
                    if df.empty:
                        return False
        by_regime = df.groupby("regime")[value_col].mean(numeric_only=True)
        if "recursive" not in by_regime.index:
            return False
        if "time_shuffled" in by_regime.index:
            return bool(by_regime["recursive"] > by_regime["time_shuffled"])
        other = by_regime.drop(index="recursive", errors="ignore")
        if other.empty:
            return False
        return bool(by_regime["recursive"] > other.max())

    def count_obs(df: pd.DataFrame, value_col: str) -> int:
        if df is None or df.empty or "observable" not in df.columns:
            return 0
        return sum(
            1
            for _, sub in df.groupby("observable")
            if pos_effect(sub, value_col)
        )

    def any_non_flat_space(df: pd.DataFrame, value_col: str) -> bool:
        """True if at least one non-PCA-2 and non-tsne2 space shows a positive effect."""
        if df is None or df.empty or "space" not in df.columns:
            return False
        for space, sub in df.groupby("space"):
            if str(space) in ("pca2", "tsne2"):
                continue
            if pos_effect(sub, value_col):
                return True
        return False

    # --- H1a: convergence ---
    basin_positive = bool(
        basin_df is not None
        and not basin_df.empty
        and basin_df["basin_score"].mean(numeric_only=True) > 0.7
    )
    dwell_positive = pos_effect(dwell_df, "mean_dwell")
    dwell_obs_count = count_obs(dwell_df, "mean_dwell")
    dwell_non_flat = any_non_flat_space(dwell_df, "mean_dwell")

    h1a_signals = {
        "basin_positive": basin_positive,
        "dwell_positive_vs_null": dwell_positive,
        "dwell_positive_in_two_observables": dwell_obs_count >= 2,
        "dwell_positive_in_non_flat_space": dwell_non_flat,
    }
    h1a_reasons = [
        f"basin mean score = {basin_df['basin_score'].mean():.3f}" if basin_df is not None and not basin_df.empty else "no basin data",
        f"dwell positive vs null: {'yes' if dwell_positive else 'no'}",
        f"dwell positive in {dwell_obs_count}/{len(observables)} observables",
        f"dwell positive in non-(pca2/tsne2) space: {'yes' if dwell_non_flat else 'no'}",
    ]
    h1a_core = sum([basin_positive, dwell_positive])
    if h1a_core >= 2 and dwell_obs_count >= 2 and dwell_non_flat:
        h1a = "strong_support"
    elif h1a_core >= 2:
        h1a = "moderate_support"
    elif h1a_core == 1:
        h1a = "weak_support"
    else:
        h1a = "not_supported"

    # --- H1b: recurrence ---
    late_rec_positive = pos_effect(late_recurrence_df, "recurrence_rate")
    late_rec_obs_count = count_obs(late_recurrence_df, "recurrence_rate")
    late_rec_non_flat = any_non_flat_space(late_recurrence_df, "recurrence_rate")

    # exit/return: positive if mean return_probability clearly > 0 for recursive
    exit_return_positive = False
    exit_return_mean = None
    if exit_return_df is not None and not exit_return_df.empty:
        if "regime" in exit_return_df.columns:
            sub = exit_return_df[exit_return_df["regime"] == "recursive"]
        else:
            sub = exit_return_df
        if not sub.empty and "return_probability" in sub.columns:
            rp = sub["return_probability"].to_numpy()
            exit_return_mean = float(rp.mean()) if len(rp) else None
            exit_return_positive = bool(exit_return_mean is not None and exit_return_mean > 0.3)

    # effect visible in a rolling window observable
    rolling_positive = False
    if late_recurrence_df is not None and not late_recurrence_df.empty:
        for obs, sub in late_recurrence_df.groupby("observable"):
            if str(obs).startswith("rolling") and pos_effect(sub, "recurrence_rate"):
                rolling_positive = True
                break

    h1b_signals = {
        "late_recurrence_above_null": late_rec_positive,
        "late_recurrence_in_two_observables": late_rec_obs_count >= 2,
        "late_recurrence_in_non_flat_space": late_rec_non_flat,
        "late_recurrence_in_rolling_window": rolling_positive,
        "exit_return_positive": exit_return_positive,
    }
    h1b_reasons = [
        f"late-time recurrence positive vs null: {'yes' if late_rec_positive else 'no'}",
        f"late-time recurrence positive in {late_rec_obs_count}/{len(observables)} observables",
        f"late-time recurrence positive in non-(pca2/tsne2) space: {'yes' if late_rec_non_flat else 'no'}",
        f"effect in rolling-window observable: {'yes' if rolling_positive else 'no'}",
        (
            f"mean return-probability (recursive): {exit_return_mean:.3f}"
            if exit_return_mean is not None
            else "no exit/return data"
        ),
    ]
    h1b_core = sum([late_rec_positive, exit_return_positive])
    if h1b_core >= 2 and late_rec_obs_count >= 2 and late_rec_non_flat and rolling_positive:
        h1b = "strong_support"
    elif h1b_core >= 2:
        h1b = "moderate_support"
    elif h1b_core == 1:
        h1b = "weak_support"
    else:
        h1b = "not_supported"

    return TwoAxisDecision(
        h1a_convergence=h1a,
        h1b_recurrence=h1b,
        h1a_reasons=h1a_reasons,
        h1b_reasons=h1b_reasons,
        h1a_signals=h1a_signals,
        h1b_signals=h1b_signals,
    )


def write_report(
    cfg: Config,
    n_trajectories: int,
    n_steps: int,
    recurrence_df: pd.DataFrame,
    dwell_df: pd.DataFrame,
    basin_df: pd.DataFrame,
    explained_variance: dict[str, list[float]],
    decision: EvidenceDecision,
    report_path: Path,
) -> Path:
    ensure_dir(report_path.parent)
    lines: list[str] = []
    lines.append(f"# LLM Attractor Experiment — {cfg.experiment_id}")
    lines.append("")
    lines.append("## Hypothesis")
    lines.append(
        "> In a bounded append-only recursive LLM loop, there exist endogenous "
        "attractor-like regimes observable in a suitable representation space."
    )
    lines.append("")
    lines.append("## Config summary")
    lines.append("")
    lines.append(f"- generation model: `{cfg.generation_model}`")
    lines.append(f"- embedding model: `{cfg.embedding_model}`")
    lines.append(f"- steps/run: {cfg.steps_per_run}")
    lines.append(f"- runs/condition: {cfg.runs_per_condition}")
    lines.append(f"- initial conditions/family: {cfg.initial_conditions_per_family}")
    lines.append(f"- temperature/top_p: {cfg.temperature}/{cfg.top_p}")
    lines.append(f"- max context chars: {cfg.max_context_chars}")
    lines.append(f"- observables: {cfg.observables}")
    lines.append(f"- PCA dims: {cfg.pca_dims}")
    lines.append(f"- baselines: {cfg.baseline_modes}")
    lines.append("")
    lines.append(f"## Data volume")
    lines.append("")
    lines.append(f"- total trajectories (recursive + baselines): {n_trajectories}")
    lines.append(f"- total steps: {n_steps}")
    lines.append("")
    lines.append("## PCA explained variance")
    lines.append("")
    for obs, evrs in explained_variance.items():
        evr_str = ", ".join(f"{v:.3f}" for v in evrs[:10])
        lines.append(f"- `{obs}`: first components → [{evr_str}]")
    lines.append("")

    lines.append("## Recurrence results")
    lines.append("")
    lines.append(_df_to_table_md(_summary_by_regime(recurrence_df, "recurrence_rate")))
    lines.append("")

    lines.append("## Dwell results")
    lines.append("")
    lines.append(_df_to_table_md(_summary_by_regime(dwell_df, "mean_dwell")))
    lines.append("")

    lines.append("## Basin results")
    lines.append("")
    if basin_df.empty:
        lines.append("_No basin results were produced (check config and clustering)._")
    else:
        lines.append(_df_to_table_md(basin_df))
    lines.append("")

    lines.append("## Evidence decision")
    lines.append("")
    lines.append(f"**Classification: `{decision.label}`**")
    lines.append("")
    lines.append("Signals:")
    for k, v in decision.signals.items():
        lines.append(f"- `{k}`: **{'yes' if v else 'no'}**")
    lines.append("")
    lines.append("Reasoning:")
    for r in decision.reasons:
        lines.append(f"- {r}")
    lines.append("")
    lines.append("## Plots")
    lines.append("")
    lines.append("See the `plots/` subdirectory for PCA trajectories, cluster occupancy, "
                 "recurrence distributions, dwell distributions, and basin plots.")
    lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def write_report_v2(
    cfg: Config,
    n_trajectories: int,
    n_steps: int,
    recurrence_df: pd.DataFrame,
    late_recurrence_df: pd.DataFrame,
    dwell_df: pd.DataFrame,
    basin_df: pd.DataFrame,
    exit_return_df: pd.DataFrame,
    basin_entry_df: pd.DataFrame,
    explained_variance: dict[str, list[float]],
    decision: TwoAxisDecision,
    decision_legacy: EvidenceDecision,
    report_path: Path,
) -> Path:
    ensure_dir(report_path.parent)
    lines: list[str] = []
    lines.append(f"# LLM Attractor Experiment — {cfg.experiment_id}")
    lines.append("")
    lines.append("## Hypotheses")
    lines.append("")
    lines.append("- **H1a (convergence)** — recursive dynamics converge to stable basin-like regions.")
    lines.append("- **H1b (recurrence)** — once inside basins, trajectories revisit neighborhoods above a temporal null.")
    lines.append("")
    lines.append("## Two-axis verdict")
    lines.append("")
    lines.append(f"- **H1a convergence: `{decision.h1a_convergence}`**")
    lines.append(f"- **H1b recurrence:  `{decision.h1b_recurrence}`**")
    lines.append("")
    lines.append("### H1a signals")
    for k, v in decision.h1a_signals.items():
        lines.append(f"- `{k}`: **{'yes' if v else 'no'}**")
    lines.append("")
    lines.append("_Reasoning:_")
    for r in decision.h1a_reasons:
        lines.append(f"- {r}")
    lines.append("")
    lines.append("### H1b signals")
    for k, v in decision.h1b_signals.items():
        lines.append(f"- `{k}`: **{'yes' if v else 'no'}**")
    lines.append("")
    lines.append("_Reasoning:_")
    for r in decision.h1b_reasons:
        lines.append(f"- {r}")
    lines.append("")
    lines.append("## Config summary")
    lines.append("")
    lines.append(f"- generation model: `{cfg.generation_model}`")
    lines.append(f"- embedding model: `{cfg.embedding_model}`")
    lines.append(f"- steps/run: {cfg.steps_per_run}")
    lines.append(f"- runs/condition: {cfg.runs_per_condition}")
    lines.append(f"- initial conditions/family: {cfg.initial_conditions_per_family}")
    lines.append(f"- temperature/top_p: {cfg.temperature}/{cfg.top_p}")
    lines.append(f"- max_output_tokens: {cfg.max_output_tokens}")
    lines.append(f"- max_context_chars: {cfg.max_context_chars}")
    lines.append(f"- observables: {cfg.observables}")
    lines.append(f"- PCA dims: {cfg.pca_dims}")
    lines.append(f"- baselines: {cfg.baseline_modes}")
    lines.append("")
    lines.append(f"## Data volume")
    lines.append("")
    lines.append(f"- total trajectories (recursive + baselines): {n_trajectories}")
    lines.append(f"- total steps: {n_steps}")
    lines.append("")
    lines.append("## PCA explained variance")
    lines.append("")
    for obs, evrs in explained_variance.items():
        evr_str = ", ".join(f"{v:.3f}" for v in evrs[:10])
        lines.append(f"- `{obs}`: first components → [{evr_str}]")
    lines.append("")

    lines.append("## Global recurrence (coarse screen)")
    lines.append("")
    lines.append(_df_to_table_md(_summary_by_regime(recurrence_df, "recurrence_rate")))
    lines.append("")

    lines.append("## Late-time recurrence (H1b primary)")
    lines.append("")
    if late_recurrence_df is None or late_recurrence_df.empty:
        lines.append("_late-time recurrence not enabled in this config._")
    else:
        lines.append(_df_to_table_md(_summary_by_regime(late_recurrence_df, "recurrence_rate")))
    lines.append("")

    lines.append("## Exit / return (H1b primary)")
    lines.append("")
    if exit_return_df is None or exit_return_df.empty:
        lines.append("_exit/return not enabled in this config._")
    else:
        agg = (
            exit_return_df.groupby(["observable", "space", "regime"], dropna=False)
            .agg(
                n=("return_probability", "count"),
                return_probability_mean=("return_probability", "mean"),
                mean_n_exits=("n_exits", "mean"),
                mean_n_returns=("n_returns", "mean"),
            )
            .reset_index()
        )
        lines.append(_df_to_table_md(agg))
    lines.append("")

    lines.append("## Basin entry times (H1a context)")
    lines.append("")
    if basin_entry_df is None or basin_entry_df.empty:
        lines.append("_basin entry not enabled in this config._")
    else:
        be = basin_entry_df[basin_entry_df["reached"] == True].copy()  # noqa: E712
        if be.empty:
            lines.append("_no runs reached the basin-entry threshold._")
        else:
            agg = (
                be.groupby(["observable", "space"], dropna=False)
                .agg(
                    n_reached=("entry_step", "count"),
                    median_entry_step=("entry_step", "median"),
                    mean_entry_step=("entry_step", "mean"),
                    mean_late_frac=("late_fraction_in_target", "mean"),
                )
                .reset_index()
            )
            lines.append(_df_to_table_md(agg))
    lines.append("")

    lines.append("## Dwell (H1a primary)")
    lines.append("")
    lines.append(_df_to_table_md(_summary_by_regime(dwell_df, "mean_dwell")))
    lines.append("")

    lines.append("## Basin (H1a primary)")
    lines.append("")
    if basin_df is None or basin_df.empty:
        lines.append("_No basin results were produced._")
    else:
        lines.append(_df_to_table_md(basin_df))
    lines.append("")

    lines.append("## Legacy single-label verdict")
    lines.append("")
    lines.append(f"**Legacy classification: `{decision_legacy.label}`** (kept for backward compat; see two-axis verdict above).")
    lines.append("")

    lines.append("## Plots")
    lines.append("")
    lines.append("See the `plots/` subdirectory.")
    lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def _summary_by_regime(df: pd.DataFrame, value_col: str) -> pd.DataFrame:
    if df.empty or value_col not in df.columns:
        return pd.DataFrame()
    group_cols = [c for c in ("regime", "observable", "space") if c in df.columns]
    if not group_cols:
        return pd.DataFrame()
    agg = (
        df.groupby(group_cols, dropna=False)[value_col]
        .agg(["mean", "std", "count"])
        .reset_index()
        .rename(columns={"mean": f"{value_col}_mean", "std": f"{value_col}_std", "count": "n"})
    )
    return agg


def _df_to_table_md(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return "_no rows_"
    try:
        return df.to_markdown(index=False, floatfmt=".4f")
    except Exception:
        return "```\n" + df.to_string(index=False) + "\n```"
