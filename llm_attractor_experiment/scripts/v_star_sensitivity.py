"""
V* numerical sensitivity grid (review weakness #5 follow-up).

The §5.10 caveat box already states that V* values are descriptive
not validation, but we have not yet quantified how sensitive V* is
to the analyst's choice of:
  - KDE bandwidth (sigma_cells in Gaussian-smoothing the density grid)
  - grid resolution (grid_n)
  - basin count (n_basins for _find_basin_centers)
  - PCA projection dimensionality (Z is always PCA-2 for the geodesic
    skeleton, but we can re-run with PCA on different fits)

This script re-runs the geodesic V* computation on the O1 perturbation
pilot under a parameter grid, reporting how mean V* shifts and whether
ordinal-agreement claims survive across parameter combinations. No
new data, no API calls.

Usage:
    python -m scripts.v_star_sensitivity

Outputs:
    data/aggregated/v_star_sensitivity.csv
    data/aggregated/v_star_sensitivity.png
"""
from __future__ import annotations

import sys
from itertools import product
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from src.experiments.dynamics.field_plots import _potential_grid  # noqa: E402
from src.experiments.perturbation.geodesic_skeleton import (  # noqa: E402
    _find_basin_centers,
    _grid_dijkstra,
)
from src.experiments.perturbation.flow_plots import _load  # noqa: E402

CONDITIONS = ("control", "neutral", "lorem", "adversarial")
EXP = "exp_perturb_O1_pilot"


def _v_star_for_condition(
    pts: np.ndarray, xb, yb, sigma_cells: float, grid_n: int, n_basins: int,
) -> dict:
    X, Y, V = _potential_grid(pts, xb, yb, grid_n=grid_n, sigma_cells=sigma_cells)
    centers = _find_basin_centers(V, n_max=n_basins)
    if len(centers) < 2:
        return {"v_star_mean": np.nan, "v_star_max": np.nan,
                "n_basins_found": len(centers), "n_geodesics": 0}
    v_stars = []
    for i in range(len(centers)):
        for j in range(i + 1, len(centers)):
            path = _grid_dijkstra(V, centers[i], centers[j])
            if not path:
                continue
            v_max = float(max(V[r, c] for r, c in path))
            v_stars.append(v_max)
    if not v_stars:
        return {"v_star_mean": np.nan, "v_star_max": np.nan,
                "n_basins_found": len(centers), "n_geodesics": 0}
    return {
        "v_star_mean": float(np.mean(v_stars)),
        "v_star_max": float(np.max(v_stars)),
        "n_basins_found": len(centers),
        "n_geodesics": len(v_stars),
    }


def main() -> int:
    exp_dir = REPO / "data" / EXP
    if not exp_dir.is_dir():
        print(f"error: {exp_dir} not found")
        return 1
    vecs, meta = _load(exp_dir, "context_tail", is_dialog=False)
    print(f"loaded {len(vecs)} embeddings for {EXP}")

    # PCA-2 (canonical for V* skeleton).
    Z = PCA(n_components=2, random_state=42).fit_transform(vecs)
    x_min, x_max = float(Z[:, 0].min()), float(Z[:, 0].max())
    y_min, y_max = float(Z[:, 1].min()), float(Z[:, 1].max())
    pad_x = 0.05 * (x_max - x_min); pad_y = 0.05 * (y_max - y_min)
    xb = (x_min - pad_x, x_max + pad_x)
    yb = (y_min - pad_y, y_max + pad_y)

    # Parameter grid.
    sigma_cells_grid = [1.0, 1.5, 2.0, 2.5, 3.0]
    grid_n_grid = [64, 96, 128]
    n_basins_grid = [3, 4, 5]

    rows = []
    n_combos = len(sigma_cells_grid) * len(grid_n_grid) * len(n_basins_grid) * len(CONDITIONS)
    print(f"computing {n_combos} (param × condition) cells...")
    for cond in CONDITIONS:
        sub_idx = (meta["regime"] == cond).values
        if sub_idx.sum() < 30:
            print(f"  skip {cond}: only {sub_idx.sum()} points")
            continue
        pts = Z[sub_idx]
        for sigma, gn, nb in product(sigma_cells_grid, grid_n_grid, n_basins_grid):
            r = _v_star_for_condition(pts, xb, yb, sigma, gn, nb)
            r.update({
                "condition": cond, "sigma_cells": sigma,
                "grid_n": gn, "n_basins_param": nb,
            })
            rows.append(r)
    out = pd.DataFrame(rows)
    out_path = REPO / "data" / "aggregated" / "v_star_sensitivity.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False)
    print(f"\nwrote {out_path}")

    # Per-condition summary: how much does V* mean shift across the grid?
    summary = out.groupby("condition").agg(
        v_star_mean_min=("v_star_mean", "min"),
        v_star_mean_median=("v_star_mean", "median"),
        v_star_mean_max=("v_star_mean", "max"),
        v_star_mean_std=("v_star_mean", "std"),
        v_star_mean_cv=("v_star_mean", lambda s: s.std() / s.mean()),
    ).reset_index()
    summary_path = REPO / "data" / "aggregated" / "v_star_sensitivity_summary.csv"
    summary.to_csv(summary_path, index=False)
    print(f"wrote {summary_path}")
    print("\n=== Per-condition V* sensitivity (across all param combinations) ===")
    print(summary.to_string(index=False))

    # Ordinal agreement: across param combinations, does the rank order
    # of conditions by V* mean stay stable?
    print("\n=== Ordinal stability of V* condition ranking across param grid ===")
    rank_records = []
    for (sigma, gn, nb), grp in out.groupby(["sigma_cells", "grid_n", "n_basins_param"]):
        rank = grp.set_index("condition")["v_star_mean"].rank(method="min").to_dict()
        rank_records.append({
            "sigma_cells": sigma, "grid_n": gn, "n_basins_param": nb,
            **{f"rank_{c}": rank.get(c, np.nan) for c in CONDITIONS},
        })
    rank_df = pd.DataFrame(rank_records)
    # Tally how often each condition has the highest / lowest V* mean.
    tally = {c: {"n_top": 0, "n_bot": 0} for c in CONDITIONS}
    for _, r in rank_df.iterrows():
        for c in CONDITIONS:
            if r[f"rank_{c}"] == 1:
                tally[c]["n_bot"] += 1
            if r[f"rank_{c}"] == 4:
                tally[c]["n_top"] += 1
    n_combos_per_cond = len(sigma_cells_grid) * len(grid_n_grid) * len(n_basins_grid)
    print(f"(n parameter combinations: {n_combos_per_cond})")
    for c in CONDITIONS:
        top_pct = 100.0 * tally[c]["n_top"] / n_combos_per_cond
        bot_pct = 100.0 * tally[c]["n_bot"] / n_combos_per_cond
        print(f"  {c:12s}  top-rank in {top_pct:.0f}% of combos, "
              f"bot-rank in {bot_pct:.0f}% of combos")

    # Plot: per condition, V* mean across the parameter grid.
    fig, ax = plt.subplots(figsize=(9, 5.5), facecolor="white")
    palette = {"control": "#1f77b4", "neutral": "#9467bd",
               "lorem": "#ff7f0e", "adversarial": "#d62728"}
    for c in CONDITIONS:
        sub = out[out["condition"] == c]
        if sub.empty:
            continue
        # Use parameter-combination index on the x-axis.
        sub = sub.assign(combo=lambda d: d.apply(
            lambda r: f"σ={r['sigma_cells']}, gn={r['grid_n']}, nb={r['n_basins_param']}",
            axis=1,
        )).sort_values(["sigma_cells", "grid_n", "n_basins_param"]).reset_index(drop=True)
        ax.plot(range(len(sub)), sub["v_star_mean"], "-o",
                color=palette.get(c, "#5fa85f"), label=c, alpha=0.8, markersize=4)
    ax.set_xlabel("parameter combination index "
                  "(σ_cells × grid_n × n_basins, sorted lexicographically)")
    ax.set_ylabel("V* mean (geodesic barrier height, log-density units)")
    ax.set_title(f"V* sensitivity across parameter grid — {EXP}\n"
                 f"({len(sigma_cells_grid)*len(grid_n_grid)*len(n_basins_grid)} parameter combos × "
                 f"{len(CONDITIONS)} conditions)")
    ax.set_facecolor("white")
    ax.grid(alpha=0.25, linewidth=0.5)
    ax.legend(loc="upper left", fontsize=9, framealpha=0.95)
    fig.tight_layout()
    fig_path = REPO / "data" / "aggregated" / "v_star_sensitivity.png"
    fig.savefig(fig_path, dpi=160, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(f"\nwrote {fig_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
