"""
Plot helpers for dynamics analysis. Produces:

  1. Regime map: scatter of λ_1_late vs SD_late per experiment, annotated with
     REPORT3 regime labels.
  2. Ensemble spread trajectory: mean pairwise run-to-run distance over time,
     one line per experiment.

Both plots write to data/dynamics_plots/ so they are discoverable at repo level
rather than buried under per-experiment dirs.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.utils.io import ensure_dir


# REPORT3 regime labels for coloring
REGIME_LABEL = {
    "exp_default": "contractive",
    "exp_long": "contractive",
    "exp_noclip": "contractive",
    "exp_op_O1_continue": "contractive",
    "exp_op_O2_paraphrase_replace": "oscillatory (2-cycle)",
    "exp_op_O3_summarize_negate": "absorbing",
    "exp_op_O3b_summarize_negate_replace": "absorbing",
    "exp_op_O4_paraphrase_append": "contractive",
    "exp_dialog_D1_curious_helpful": "stylistic multi-basin",
    "exp_dialog_D2_replace_curious_helpful": "stylistic multi-basin",
    "exp_dialog_D3_debate_advocate_skeptic": "contractive (debate)",
    # publication-scale experiments
    "exp_pub_O1_continue": "contractive",
    "exp_pub_O2_paraphrase_replace": "oscillatory (2-cycle)",
    "exp_pub_O3_summarize_negate_replace": "absorbing",
    "exp_pub_D1_dialog_curious_helpful": "stylistic multi-basin",
    "exp_pub_D1_dialog_curious_helpful_v2": "stylistic multi-basin",
}

REGIME_COLOR = {
    "contractive": "#4a90e2",
    "contractive (debate)": "#1f4e79",
    "absorbing": "#8b5cf6",
    "oscillatory (2-cycle)": "#e24a4a",
    "stylistic multi-basin": "#5fa85f",
}

# Short display labels
DISPLAY = {
    "exp_default": "exp_default",
    "exp_long": "exp_long",
    "exp_noclip": "exp_noclip",
    "exp_op_O1_continue": "O1",
    "exp_op_O2_paraphrase_replace": "O2",
    "exp_op_O3_summarize_negate": "O3",
    "exp_op_O3b_summarize_negate_replace": "O3b",
    "exp_op_O4_paraphrase_append": "O4",
    "exp_dialog_D1_curious_helpful": "D1",
    "exp_dialog_D2_replace_curious_helpful": "D2",
    "exp_dialog_D3_debate_advocate_skeptic": "D3",
    # publication-scale experiments
    "exp_pub_O1_continue": "O1_pub",
    "exp_pub_O2_paraphrase_replace": "O2_pub",
    "exp_pub_O3_summarize_negate_replace": "O3_pub",
    "exp_pub_D1_dialog_curious_helpful": "D1_pub (20-step)",
    "exp_pub_D1_dialog_curious_helpful_v2": "D1_pub (40-step)",
}


def regime_map(cross_csv: Path, out_dir: Path, observable: str = "rolling_k3") -> Path:
    """
    Scatter plot of (λ_1_late, SD_late) per experiment, color-coded by regime.
    One point per experiment (mean across (family, IC) groups).
    """
    df = pd.read_csv(cross_csv)
    if "lambda_1_late" not in df.columns:
        # Backward compat — try old schema
        if "lambda_1" in df.columns:
            raise ValueError(
                f"{cross_csv} is from the old pipeline (no lambda_1_late); "
                f"rerun `python -m src.experiments.dynamics.analyze --all`"
            )
        raise ValueError(f"{cross_csv} missing lambda_1_late")

    sub = df[(df["regime"] == "recursive") & (df["observable"] == observable)]
    if sub.empty:
        raise ValueError(f"no rows for regime=recursive, observable={observable}")

    agg = (
        sub.groupby("experiment_id")
        .agg(
            lam1=("lambda_1_late", "mean"),
            lam1_std=("lambda_1_late", "std"),
            sd=("sharpness_dim_late", "mean"),
            sd_std=("sharpness_dim_late", "std"),
        )
        .reset_index()
    )

    fig, ax = plt.subplots(figsize=(9, 6))
    for _, row in agg.iterrows():
        exp = row["experiment_id"]
        regime = REGIME_LABEL.get(exp, "unknown")
        color = REGIME_COLOR.get(regime, "#888")
        ax.errorbar(
            row["lam1"],
            row["sd"],
            xerr=row["lam1_std"] if pd.notna(row["lam1_std"]) else 0,
            yerr=row["sd_std"] if pd.notna(row["sd_std"]) else 0,
            fmt="o",
            color=color,
            markersize=9,
            capsize=3,
            alpha=0.9,
            label=regime,
        )
        ax.annotate(
            DISPLAY.get(exp, exp),
            xy=(row["lam1"], row["sd"]),
            xytext=(6, 6),
            textcoords="offset points",
            fontsize=9,
        )

    ax.axvline(0, color="k", lw=0.5, alpha=0.5, linestyle="--")
    ax.text(
        0.001,
        ax.get_ylim()[0] + 0.05 if ax.get_ylim()[0] > 0 else 0.1,
        "edge of stability →",
        fontsize=8,
        alpha=0.6,
    )
    ax.set_xlabel(r"$\lambda_1$ (late; t_baseline = T/2)")
    ax.set_ylabel("Sharpness Dimension (late)")
    ax.set_title(f"Regime map: ({observable}) across 11 experiments")
    ax.grid(alpha=0.2)

    # Dedup legend
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), loc="lower left", fontsize=8)

    ensure_dir(out_dir)
    path = out_dir / f"regime_map_{observable}.png"
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    return path


def spread_trajectories(
    data_dir: Path, out_dir: Path, observable: str = "rolling_k3"
) -> Path:
    """
    Plot mean pairwise run-to-run distance over time for each experiment.
    Reads spread_t1 / spread_mid / spread_last from per-experiment dynamics.csv.

    Uses just 3 timepoints per experiment since dynamics.csv only persists
    those. A richer version would reload embeddings to get the full trajectory.
    """
    rows = []
    for exp_dir in sorted(data_dir.iterdir()):
        if not exp_dir.is_dir():
            continue
        dyn_csv = exp_dir / "metrics" / "dynamics.csv"
        if not dyn_csv.exists():
            continue
        df = pd.read_csv(dyn_csv)
        sub = df[(df["regime"] == "recursive") & (df["observable"] == observable)]
        if sub.empty:
            continue
        rows.append(
            {
                "experiment_id": exp_dir.name,
                "t1": sub["spread_t1"].mean(),
                "mid": sub["spread_mid"].mean() if "spread_mid" in sub.columns else np.nan,
                "last": sub["spread_last"].mean(),
            }
        )
    if not rows:
        return out_dir / f"spread_trajectories_{observable}.png"

    fig, ax = plt.subplots(figsize=(9, 5))
    for r in rows:
        exp = r["experiment_id"]
        regime = REGIME_LABEL.get(exp, "unknown")
        color = REGIME_COLOR.get(regime, "#888")
        x = [1, "mid", "end"]
        y = [r["t1"], r["mid"], r["last"]]
        ax.plot(
            range(3),
            y,
            "o-",
            color=color,
            label=DISPLAY.get(exp, exp),
            alpha=0.85,
            lw=1.5,
        )
    ax.set_xticks(range(3))
    ax.set_xticklabels(["t=1", "t=T/2", "t=T-1"])
    ax.set_ylabel("mean pairwise run-to-run distance")
    ax.set_title(f"Ensemble spread trajectory ({observable}) — 11 experiments")
    ax.legend(loc="best", fontsize=7, ncols=2)
    ax.grid(alpha=0.2)

    ensure_dir(out_dir)
    path = out_dir / f"spread_trajectories_{observable}.png"
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    return path


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(prog="dynamics_plots")
    parser.add_argument("--cross-csv", default="data/aggregated/dynamics_cross_experiment.csv")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--out-dir", default="data/aggregated/dynamics_plots")
    parser.add_argument("--observable", default="rolling_k3")
    args = parser.parse_args()

    p1 = regime_map(Path(args.cross_csv), Path(args.out_dir), observable=args.observable)
    p2 = spread_trajectories(Path(args.data_dir), Path(args.out_dir), observable=args.observable)
    print(f"wrote {p1}")
    print(f"wrote {p2}")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
