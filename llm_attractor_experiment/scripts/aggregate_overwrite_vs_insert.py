"""Aggregate overwrite-vs-insert switching across O1 (append), O2 (oscillatory
replace), and O3 (absorbing replace) into a single CSV and a 2-panel
comparison plot.

Output: data/aggregated/overwrite_vs_insert_cross_regime/
  - cross_regime.csv          (long-form, regime x mode x dose x rate x CI)
  - cross_regime.png          (2-panel grouped bar chart, dose 80 / dose 200)

Used as Fig 5 in §5.2.1 (round-32, F3 cross-loop insert validation).
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT_DIR = DATA / "aggregated" / "overwrite_vs_insert_cross_regime"

REGIMES = [
    ("O1", "exp_perturb_O1_overwrite_vs_insert", "append"),
    ("O2", "exp_perturb_O2_overwrite_vs_insert", "replace"),
    ("O3", "exp_perturb_O3_overwrite_vs_insert", "replace"),
]
DOSES = [80, 200]
MODES = ["overwrite", "insert"]


def _load_one(regime: str, exp_dir: str, loop: str) -> pd.DataFrame:
    csv = DATA / exp_dir / "reports" / "perturbation" / "switching_summary.csv"
    df = pd.read_csv(csv)
    rows = []
    for dose in DOSES:
        ow_cond = f"adversarial_dose{dose}"
        ins_cond = f"adversarial_insert_dose{dose}"
        for mode, cond in [("overwrite", ow_cond), ("insert", ins_cond)]:
            r = df.loc[df["condition"] == cond].iloc[0]
            rows.append({
                "regime": regime,
                "loop_mode": loop,
                "dose": dose,
                "mode": mode,
                "switch_rate": float(r["switch_rate"]),
                "n_switched": int(r["n_switched"]),
                "n_total": int(r["n_total"]),
                "ci_lo": float(r["switch_rate_ci_lo"]),
                "ci_hi": float(r["switch_rate_ci_hi"]),
            })
    return pd.DataFrame(rows)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    parts = [_load_one(r, d, l) for r, d, l in REGIMES]
    df = pd.concat(parts, ignore_index=True)
    csv_path = OUT_DIR / "cross_regime.csv"
    df.to_csv(csv_path, index=False)
    print(f"wrote {csv_path}")

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), sharey=True)
    regime_colors = {
        "O1": "#1f77b4",
        "O2": "#d62728",
        "O3": "#9467bd",
    }
    mode_alpha = {"overwrite": 0.95, "insert": 0.45}
    mode_hatch = {"overwrite": "", "insert": "//"}

    for ax, dose in zip(axes, DOSES):
        sub = df.loc[df["dose"] == dose].copy()
        regimes = ["O1", "O2", "O3"]
        x = np.arange(len(regimes))
        bar_w = 0.36

        for i, mode in enumerate(MODES):
            heights = []
            err_lo = []
            err_hi = []
            colors = []
            for reg in regimes:
                row = sub.loc[(sub["regime"] == reg) & (sub["mode"] == mode)].iloc[0]
                heights.append(row["switch_rate"])
                err_lo.append(row["switch_rate"] - row["ci_lo"])
                err_hi.append(row["ci_hi"] - row["switch_rate"])
                colors.append(regime_colors[reg])
            xpos = x + (i - 0.5) * bar_w
            bars = ax.bar(
                xpos, heights, width=bar_w, color=colors,
                alpha=mode_alpha[mode], edgecolor="black", linewidth=0.6,
                hatch=mode_hatch[mode], label=mode,
            )
            ax.errorbar(
                xpos, heights, yerr=[err_lo, err_hi],
                fmt="none", ecolor="black", capsize=3, linewidth=1,
            )
            for xp, h in zip(xpos, heights):
                ax.text(xp, h + 0.025, f"{h:.2f}", ha="center", va="bottom", fontsize=8)

        ax.set_xticks(x)
        ax.set_xticklabels(
            [f"{r}\n({l})" for r, l in zip(
                regimes, ["append", "oscillatory\nreplace", "absorbing\nreplace"])],
            fontsize=9,
        )
        ax.set_ylim(0, 1.08)
        ax.set_title(f"adversarial dose = {dose} tokens", fontsize=11)
        ax.axhline(0.5, color="grey", linestyle=":", linewidth=0.8, zorder=0)
        ax.grid(axis="y", linestyle=":", alpha=0.4)

    axes[0].set_ylabel("switching rate (Wilson 95% CI)")

    ow_patch = plt.Rectangle((0, 0), 1, 1, facecolor="#888888", alpha=0.95,
                             edgecolor="black", label="state-reset overwrite")
    in_patch = plt.Rectangle((0, 0), 1, 1, facecolor="#888888", alpha=0.45,
                             edgecolor="black", hatch="//", label="insert")
    fig.legend(
        handles=[ow_patch, in_patch],
        loc="upper center", ncol=2, frameon=False,
        bbox_to_anchor=(0.5, 1.01), fontsize=9,
    )
    fig.suptitle(
        "Overwrite-vs-insert switching across loop modes "
        "(O1 append, O2/O3 replace; n=50/cell)",
        y=1.06, fontsize=11,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    png_path = OUT_DIR / "cross_regime.png"
    fig.savefig(png_path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {png_path}")


if __name__ == "__main__":
    main()
