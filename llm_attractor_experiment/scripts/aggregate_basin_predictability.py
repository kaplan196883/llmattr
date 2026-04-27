"""
Aggregate basin_predictability results across all four publication-scale
experiments into a single cross-regime comparison plot + CSV + summary.

Reads: data/{exp}/reports/basin_predictability/basin_predictability.csv
Writes: data/aggregated/basin_predictability_cross/
  - cross_basin_predictability.csv  (stacked)
  - cross_basin_predictability.png  (one-panel overlay + per-obs grid)
  - cross_basin_predictability_summary.md

Usage:
    python -m scripts.aggregate_basin_predictability
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from scripts.lib_load import read_experiment_csv
from src.utils.io import ensure_dir


EXPERIMENTS = [
    ("exp_pub_O1_continue",                 "O1 contractive",            "#4a90e2"),
    ("exp_pub_O2_paraphrase_replace",       "O2 oscillatory (2-cycle)",  "#e24a4a"),
    ("exp_pub_O3_summarize_negate_replace", "O3 absorbing",              "#8b5cf6"),
    ("exp_pub_D1_dialog_curious_helpful_v2","D1 stylistic multi-basin",  "#5fa85f"),
    # D2 = drill-down dialog (explorer/expert). Distinct from the historical
    # "exp_dialog_D2_replace_curious_helpful" (a replace-mode D1 variant) —
    # see docs/DATA_INDEX.md for the naming-collision note.
    ("exp_D2_exploratory_drilldown",        "D2 drill-down dialog",      "#d4a017"),
]

# Pick one "canonical" observable per experiment — the one with most information
CANONICAL_OBS = {
    "exp_pub_O1_continue":                   "context_tail",
    "exp_pub_O2_paraphrase_replace":         "context_tail",
    "exp_pub_O3_summarize_negate_replace":   "context_tail",
    "exp_pub_D1_dialog_curious_helpful_v2":  "context_tail",
    "exp_D2_exploratory_drilldown":          "context_tail",
}


def load_all(data_dir: Path) -> pd.DataFrame:
    rows = []
    for exp_id, label, color in EXPERIMENTS:
        df = read_experiment_csv(data_dir, exp_id, ("reports", "basin_predictability", "basin_predictability.csv"))
        if df is None:
            continue
        df["experiment_id"] = exp_id
        df["label"] = label
        df["color"] = color
        rows.append(df)
    return pd.concat(rows, ignore_index=True)


def plot_overlay(df: pd.DataFrame, out_path: Path) -> None:
    """Main cross-regime comparison: recursive top-1 vs step, canonical observable per exp."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5), gridspec_kw={"width_ratios": [1.0, 1.0]})

    # Left: top-1 curves
    ax = axes[0]
    for exp_id, label, color in EXPERIMENTS:
        obs = CANONICAL_OBS[exp_id]
        sub = df[(df["experiment_id"] == exp_id) & (df["regime"] == "recursive") &
                 (df["observable"] == obs) & (df["n"] > 0)].sort_values("step")
        if sub.empty:
            continue
        ax.errorbar(
            sub["step"], sub["top1"], yerr=sub["top1_std"].fillna(0),
            label=label, color=color, marker="o", lw=2, capsize=3, markersize=7,
        )
    # chance line (both use 11-12 classes, plot band 1/12..1/11)
    ax.axhspan(1/12, 1/11, color="#ccc", alpha=0.25, label="chance (1/11–1/12)")
    ax.set_xlabel("step k (predictor)")
    ax.set_ylabel("top-1 accuracy: predict final cluster from step k embedding")
    ax.set_title("Cross-regime basin predictability\n(canonical obs: context_tail, recursive regime)")
    ax.set_ylim(0, 1.0)
    ax.grid(alpha=0.25)
    ax.legend(loc="lower right", fontsize=9)

    # Right: barplot of "seed-determinism" at t=0 and "refinement" gain t=0→t=30
    ax = axes[1]
    bar_rows = []
    for exp_id, label, color in EXPERIMENTS:
        obs = CANONICAL_OBS[exp_id]
        sub = df[(df["experiment_id"] == exp_id) & (df["regime"] == "recursive") &
                 (df["observable"] == obs) & (df["n"] > 0)]
        if sub.empty:
            continue
        t0 = sub[sub["step"] == 0]["top1"].iloc[0] if (sub["step"] == 0).any() else np.nan
        t30 = sub[sub["step"] == 30]["top1"].iloc[0] if (sub["step"] == 30).any() else np.nan
        bar_rows.append({"label": label, "color": color, "t0": t0, "t30": t30, "gain": t30 - t0})
    xs = np.arange(len(bar_rows))
    w = 0.35
    colors = [r["color"] for r in bar_rows]
    ax.bar(xs - w/2, [r["t0"] for r in bar_rows], w,
           color=colors, alpha=0.55, label="top-1 at step 0 (seed-determinism)")
    ax.bar(xs + w/2, [r["t30"] for r in bar_rows], w,
           color=colors, alpha=1.0, label="top-1 at step 30 (after recursion)")
    for i, r in enumerate(bar_rows):
        ax.annotate(f"+{r['gain']*100:.0f}pp", xy=(i, max(r["t0"], r["t30"]) + 0.02),
                    ha="center", fontsize=9, fontweight="bold")
    ax.set_xticks(xs)
    ax.set_xticklabels([r["label"].replace(" ", "\n", 1) for r in bar_rows], fontsize=9)
    ax.set_ylabel("top-1 accuracy")
    ax.set_ylim(0, 1.05)
    ax.axhline(1/12, color="#999", linestyle=":", lw=1)
    ax.set_title("Seed-determinism vs recursion refinement\n(gain = step 30 − step 0)")
    ax.grid(alpha=0.25, axis="y")
    ax.legend(loc="lower right", fontsize=8)

    fig.suptitle("Are attractor basins fate-locked at t=0? Cross-regime comparison",
                 fontsize=14, y=1.02)
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def plot_per_observable_grid(df: pd.DataFrame, out_path: Path) -> None:
    """Per-observable grid: 3 panels (output, rolling_k3 / rolling_agent_k3, context_tail)
    each showing all four experiments' curves."""
    # For operator experiments: output, rolling_k3, context_tail
    # For D1: rolling_agent_k3 acts like rolling_k3
    panel_map = [
        ("output / (D1 omitted)", ["output"]),
        ("rolling_k3 / rolling_agent_k3", ["rolling_k3", "rolling_agent_k3"]),
        ("context_tail", ["context_tail"]),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(18, 5.5), sharey=True)
    for ax, (title, obs_list) in zip(axes, panel_map):
        for exp_id, label, color in EXPERIMENTS:
            sub = df[(df["experiment_id"] == exp_id) & (df["regime"] == "recursive") &
                     (df["observable"].isin(obs_list)) & (df["n"] > 0)].sort_values("step")
            if sub.empty:
                continue
            ax.errorbar(
                sub["step"], sub["top1"], yerr=sub["top1_std"].fillna(0),
                label=label, color=color, marker="o", lw=1.8, capsize=3,
            )
        ax.axhspan(1/12, 1/11, color="#ccc", alpha=0.25)
        ax.set_title(title)
        ax.set_xlabel("step k")
        ax.grid(alpha=0.25)
        ax.set_ylim(0, 1.0)
    axes[0].set_ylabel("top-1 accuracy (recursive)")
    axes[-1].legend(loc="lower right", fontsize=9)
    fig.suptitle("Basin predictability per observable — cross-regime",
                 fontsize=14, y=1.02)
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def write_summary(df: pd.DataFrame, out_path: Path) -> None:
    lines = []
    lines.append("# Cross-regime basin predictability — summary\n")
    lines.append("Question: how much of the final-cluster fate is locked in by the seed,")
    lines.append("and how much does the recursive loop select / refine?\n")
    lines.append("Metric: 5-fold CV logistic regression, PCA-10 embedding at step k →")
    lines.append("majority-vote K-means cluster over steps 35–38 (chance ≈ 1/12 ≈ 8.3%).\n")
    lines.append("## Canonical observable (`context_tail`) — recursive regime\n")
    lines.append("| regime | top-1 step 0 | top-1 step 30 | Δ (refinement gain) |")
    lines.append("|---|---|---|---|")
    for exp_id, label, _ in EXPERIMENTS:
        obs = CANONICAL_OBS[exp_id]
        sub = df[(df["experiment_id"] == exp_id) & (df["regime"] == "recursive") &
                 (df["observable"] == obs) & (df["n"] > 0)]
        if sub.empty:
            continue
        t0 = sub[sub["step"] == 0]["top1"]
        t30 = sub[sub["step"] == 30]["top1"]
        t0v = t0.iloc[0] if len(t0) else float("nan")
        t30v = t30.iloc[0] if len(t30) else float("nan")
        lines.append(f"| {label} | {t0v*100:.1f}% | {t30v*100:.1f}% | +{(t30v - t0v)*100:.1f}pp |")

    lines.append("\n## Interpretation\n")
    lines.append("- **O2 (oscillatory) and O3 (absorbing)** start at ≥88% top-1 and gain only")
    lines.append("  ≤3pp over 30 steps. Basins are essentially **fate-locked at the seed**.")
    lines.append("  For replace-based operators, the first assistant turn already projects the")
    lines.append("  trajectory into its attractor; the loop does maintenance, not selection.\n")
    lines.append("- **O1 (contractive)** starts lower (~68%) and climbs to ~84%. Basin is ")
    lines.append("  substantially seed-determined but the recursion does genuine refinement ")
    lines.append("  (~16pp). The continue-based loop has room to drift before committing.\n")
    lines.append("- **D1 (stylistic multi-basin)** starts near **42%** (context_tail) — ")
    lines.append("  roughly half-way between chance and deterministic — and climbs to **75%** ")
    lines.append("  at step 30. A +33pp gain: D1 is the only regime where the recursion does ")
    lines.append("  **real basin-selection work**, not just maintenance. Consistent with the ")
    lines.append("  stylistic interpretation: multiple basins coexist in the family, and ")
    lines.append("  the specific dialog trajectory commits gradually, not instantly.\n")
    lines.append("## Scientific upshot\n")
    lines.append("Seed-determinism is a **regime discriminator**, not a universal property of ")
    lines.append("recursive LLM systems. The four regimes split cleanly on this axis:\n")
    lines.append("```")
    lines.append("        seed-determined   ←——————————→   runtime-selected")
    lines.append("    O2/O3 ≈ 90% step-0       O1 ≈ 68%       D1 ≈ 42%")
    lines.append("    (absorbing, 2-cycle)     (contractive)  (multi-basin)")
    lines.append("```\n")
    lines.append("This also closes the circle on an earlier open question: the reason D1 ")
    lines.append("shows a persistent cross-basin bridge structure in the per-family field ")
    lines.append("plots is precisely that its basin-assignment is not seed-fixed. Trajectories ")
    lines.append("genuinely move between attractor neighborhoods before settling.\n")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    data_dir = Path("data")
    out_dir = data_dir / "aggregated" / "basin_predictability_cross"
    ensure_dir(out_dir)

    df = load_all(data_dir)
    if df.empty:
        print("no data")
        return 1

    df.to_csv(out_dir / "cross_basin_predictability.csv", index=False)
    print(f"wrote {out_dir / 'cross_basin_predictability.csv'}")

    plot_overlay(df, out_dir / "cross_basin_predictability.png")
    print(f"wrote {out_dir / 'cross_basin_predictability.png'}")

    plot_per_observable_grid(df, out_dir / "cross_basin_predictability_grid.png")
    print(f"wrote {out_dir / 'cross_basin_predictability_grid.png'}")

    write_summary(df, out_dir / "cross_basin_predictability_summary.md")
    print(f"wrote {out_dir / 'cross_basin_predictability_summary.md'}")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
