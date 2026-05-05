"""Plot the §5.1.3 dip-vs-terminal-step decay.

Source: data/aggregated/dip_mechanism_B/persistence_by_terminal_step_v2.csv
        data/aggregated/dip_mechanism_B/dip_contrast_ci.csv

Two panels:
  (A) Per-dose destination-coherent persistence vs terminal step T,
      under the frozen canonical PCA + K-means k=12 cluster basis. Shows
      doses 1500/2000/3000 with Wilson 95% CIs at each terminal step.
      The visual story: 1500 and 3000 stay flat-ish; 2000 climbs over T.
      Vertical line at T=29 marks the original measurement horizon.
  (B) Dip contrast Delta(T) = S_2000(T) - 0.5*(S_1500(T) + S_3000(T))
      under both frozen-canonical and joint bases, with family-cluster
      bootstrap 95% CIs. Visualizes the closure of the dip toward zero.
"""
from __future__ import annotations

from math import sqrt
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DIP_DIR = ROOT / "data" / "aggregated" / "dip_mechanism_B"
OUT_PATH = DIP_DIR / "dip_vs_terminal_step.png"


def _wilson(p: float, n: int) -> tuple[float, float]:
    if n <= 0:
        return float("nan"), float("nan")
    z = 1.959963984540054
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, center - half), min(1.0, center + half)


def main() -> None:
    by_t = pd.read_csv(DIP_DIR / "persistence_by_terminal_step_v2.csv")
    ci_df = pd.read_csv(DIP_DIR / "dip_contrast_ci.csv")

    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(13, 4.7))

    # =============================================================
    # Panel A: per-dose persistence vs T, frozen canonical basis
    # =============================================================
    sub = by_t[by_t["basis"] == "frozen"].copy()
    dose_styles = [
        (1500, "#1f77b4", "o", "dose 1500"),
        (2000, "#d62728", "s", "dose 2000"),
        (3000, "#2ca02c", "^", "dose 3000"),
    ]
    for dose, color, marker, label in dose_styles:
        d = sub[sub["dose"] == dose].sort_values("terminal_step")
        if d.empty:
            continue
        x = d["terminal_step"].to_numpy()
        y = d["S_dst"].to_numpy()
        n = d["n_kicked"].to_numpy()
        cis = [_wilson(p, int(nn)) for p, nn in zip(y, n)]
        lo = np.array([c[0] for c in cis])
        hi = np.array([c[1] for c in cis])
        ax_a.errorbar(x, y, yerr=[y - lo, hi - y], fmt=f"{marker}-",
                      color=color, lw=1.6, markersize=7, capsize=3, label=label)
    ax_a.axvline(29, color="black", linestyle="--", lw=0.8, alpha=0.55)
    ax_a.text(29, 0.98, "  canonical T=29", ha="left", va="top",
              fontsize=8, color="black", alpha=0.7)
    ax_a.set_xlabel("terminal step T (injection at t=15, append-mode)")
    ax_a.set_ylabel("destination-coherent persistence (Wilson 95% CI)")
    ax_a.set_xticks([29, 40, 50, 60, 70, 79])
    ax_a.set_xticklabels(["29", "40", "50", "60", "70", "79"])
    ax_a.set_ylim(0, 1.0)
    ax_a.grid(axis="y", linestyle=":", alpha=0.4)
    ax_a.set_title(
        "(A) Per-dose persistence vs terminal step\n"
        "(frozen canonical PCA + K-means k=12, n=100/cell)",
        fontsize=10,
    )
    ax_a.legend(fontsize=9, loc="lower right")

    # =============================================================
    # Panel B: dip contrast Delta(T) for both bases
    # =============================================================
    basis_styles = [
        ("frozen", "#d62728", "o", "frozen canonical basis"),
        ("joint",  "#7f7f7f", "s", "joint basis (sensitivity check)"),
    ]
    for basis, color, marker, label in basis_styles:
        d = ci_df[ci_df["basis"] == basis].sort_values("terminal_step")
        if d.empty:
            continue
        x = d["terminal_step"].to_numpy()
        y = d["delta_point"].to_numpy()
        lo = d["delta_lo_95"].to_numpy()
        hi = d["delta_hi_95"].to_numpy()
        ax_b.errorbar(x, y, yerr=[y - lo, hi - y], fmt=f"{marker}-",
                      color=color, lw=1.6, markersize=7, capsize=3, label=label)
    ax_b.axhline(0.0, color="black", linestyle="-", lw=0.7, alpha=0.5)
    ax_b.axvline(29, color="black", linestyle="--", lw=0.8, alpha=0.55)
    ax_b.text(29, -0.03, "  canonical T=29", ha="left", va="top",
              fontsize=8, color="black", alpha=0.7)
    ax_b.set_xlabel("terminal step T")
    ax_b.set_ylabel(
        r"dip contrast $\Delta(T) = S^{dst}_{2000} - \frac{1}{2}(S^{dst}_{1500} + S^{dst}_{3000})$"
    )
    ax_b.set_xticks([29, 40, 50, 60, 70, 79])
    ax_b.set_xticklabels(["29", "40", "50", "60", "70", "79"])
    ax_b.set_ylim(-0.32, 0.12)
    ax_b.grid(axis="y", linestyle=":", alpha=0.4)
    ax_b.set_title(
        "(B) Dip contrast $\\Delta(T)$ vs terminal step\n"
        "(family-cluster bootstrap 95% CI)",
        fontsize=10,
    )
    ax_b.legend(fontsize=9, loc="lower right")

    fig.suptitle(
        "Long-horizon decay of the high-dose destination-coherent dip "
        "($n=100$ per cell, doses 1500/2000/3000)",
        fontsize=11.5,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(OUT_PATH, dpi=160, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
