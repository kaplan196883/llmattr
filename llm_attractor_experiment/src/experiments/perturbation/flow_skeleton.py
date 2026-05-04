"""
Combined V-landscape + dynamic flow + geodesic skeleton visualization.

Layers (back to front):
  1. V(x) = -log ρ(x) contour fill (magma_r): static potential.
  2. Streamlines (white): actual per-step displacement field, showing how
     trajectories *flow* over the V landscape — independent of geodesics.
  3. Basin centers (★): local V minima.
  4. Dijkstra geodesics between basin pairs, with V* (max-V along path)
     annotations: the static minimum-action skeleton for comparison with
     the dynamic flow.

The geodesic is the "shortest path through the potential" computed from
density alone. The streamline is "the path actual trajectories take",
computed from one-step transitions. Where these agree, the system is
gradient-flow; where they diverge, there's a non-conservative component
(circulation, drift). For O2's 2-cycle this is the most diagnostic
signature: streamlines circulate even when geodesics don't.

Output:
  data/<exp>/reports/perturbation/flow_skeleton_pca.png
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

from src.experiments.dynamics.field_plots import _clean_uv_for_streamplot
from src.experiments.perturbation.field_plots import _compute_per_condition_fields
from src.experiments.perturbation.flow_plots import _load
from src.experiments.perturbation.geodesic_skeleton import (
    _find_basin_centers, _grid_dijkstra, _potential_grid,
)
from src.utils.io import ensure_dir
from src.utils.logging import get_logger, setup_logging

log = get_logger(__name__)


CONDITIONS = ["control", "neutral", "lorem", "adversarial"]
COND_COLORS = {"control": "#4a90e2", "neutral": "#8b5cf6",
               "lorem": "#ff9800", "adversarial": "#d62728"}

DPI = 220


def _draw_panel(
    ax, X, Y, V, flow_field, pts, cond, n_basins=4,
):
    color = COND_COLORS.get(cond, "#5fa85f")

    # 1. V contour background
    ax.contourf(X, Y, V, levels=20, cmap="magma", alpha=0.55)
    ax.contour(X, Y, V, levels=10, colors="#555", linewidths=0.3, alpha=0.4)

    # 2. Flow streamlines on top (dark grey, semi-transparent)
    if flow_field is not None:
        Xf, Yf, U, V_flow, density, _ = flow_field
        U2, V2 = _clean_uv_for_streamplot(Xf, Yf, U, V_flow, density)
        if (np.sqrt(U2**2 + V2**2) > 0).sum() > 10:
            ax.streamplot(
                Xf, Yf, U2, V2,
                color="#1f1f1f", linewidth=0.9, density=1.6, arrowsize=1.0,
                arrowstyle="-|>",
            )

    # Background scatter (dark dots, very transparent)
    ax.scatter(pts[:, 0], pts[:, 1], s=0.4, alpha=0.10, color="#222", linewidths=0)

    # 3. Basin centers
    centers = _find_basin_centers(V, n_max=n_basins)
    for (r, c) in centers:
        ax.scatter(X[r, c], Y[r, c], s=140, marker="*",
                   color=color, edgecolors="black", linewidths=1.0, zorder=12)

    # 4. Geodesics between basin pairs
    barriers = []
    for i in range(len(centers)):
        for j in range(i + 1, len(centers)):
            path = _grid_dijkstra(V, centers[i], centers[j])
            if not path:
                continue
            xs = np.array([X[r, c] for r, c in path])
            ys = np.array([Y[r, c] for r, c in path])
            v_path = np.array([V[r, c] for r, c in path])
            v_max = float(v_path.max())
            barriers.append(v_max)
            ax.plot(xs, ys, color=color, lw=1.5, alpha=0.95, zorder=10)
            mid = len(path) // 2
            ax.annotate(
                f"V*={v_max:.1f}",
                xy=(xs[mid], ys[mid]),
                xytext=(6, 6), textcoords="offset points",
                fontsize=8, color=color,
                bbox=dict(boxstyle="round,pad=0.2",
                          fc="white", ec=color, alpha=0.9, lw=0.6),
                zorder=14,
            )

    bar_summary = ""
    if barriers:
        bar_summary = (f", V*∈[{min(barriers):.1f}, {max(barriers):.1f}]")
    ax.set_title(
        f"{cond}  ({len(centers)} basins{bar_summary})",
        fontsize=11, color=color,
    )
    ax.set_xlabel("PCA-1")
    ax.set_ylabel("PCA-2")


def render_flow_skeleton_for_pilot(
    exp_dir: Path, observable: str, is_dialog: bool,
    grid_n_v: int = 96, grid_n_flow: int = 32, n_basins: int = 4,
    conditions: list[str] | None = None,
) -> None:
    vecs, meta = _load(exp_dir, observable, is_dialog)
    log.info("loaded %d points for %s", len(vecs), exp_dir.name)

    out_dir = exp_dir / "reports" / "perturbation"
    ensure_dir(out_dir)

    if conditions is None:
        conditions = CONDITIONS

    Z = PCA(n_components=2, random_state=42).fit_transform(vecs)
    x_min, x_max = float(Z[:, 0].min()), float(Z[:, 0].max())
    y_min, y_max = float(Z[:, 1].min()), float(Z[:, 1].max())
    xpad = 0.05 * (x_max - x_min + 1e-9)
    ypad = 0.05 * (y_max - y_min + 1e-9)
    xb = (x_min - xpad, x_max + xpad)
    yb = (y_min - ypad, y_max + ypad)

    flow_fields = _compute_per_condition_fields(
        Z, meta, grid_n=grid_n_flow, conditions=conditions,
    )

    n = len(conditions)
    if n <= 2:
        n_rows, n_cols = 1, n
    elif n <= 4:
        n_rows, n_cols = 2, 2
    else:
        n_cols = 3
        n_rows = (n + n_cols - 1) // n_cols
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(8 * n_cols, 6.5 * n_rows),
                             sharex=True, sharey=True, squeeze=False)
    for ax, cond in zip(axes.flat, conditions):
        sub_idx = (meta["regime"] == cond).values
        if sub_idx.sum() < 30:
            ax.set_title(f"{cond} (no data)")
            continue
        pts = Z[sub_idx]
        X, Y, V = _potential_grid(pts, xb, yb, grid_n=grid_n_v)
        flow_field = flow_fields.get(cond)
        _draw_panel(ax, X, Y, V, flow_field, pts, cond, n_basins=n_basins)
        ax.set_xlim(xb); ax.set_ylim(yb)
        ax.grid(alpha=0.15)
    # Hide unused panels
    for ax in axes.flat[n:]:
        ax.set_visible(False)

    fig.suptitle(
        "Flow + skeleton: V landscape, dynamic flow streamlines, basin geodesics  (PCA-2)\n"
        "background = V = −log ρ  |  dark streamlines = actual trajectory flow  "
        "|  ★ = basin density-peak  |  curves = static minimum-action geodesics",
        fontsize=13, y=1.00,
    )
    p = out_dir / "flow_skeleton_pca.png"
    fig.savefig(p, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    log.info("wrote %s", p)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="perturb_flow_skeleton")
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--observable", default="context_tail")
    parser.add_argument("--is-dialog", action="store_true")
    parser.add_argument("--n-basins", type=int, default=4)
    parser.add_argument("--grid-n-v", type=int, default=96)
    parser.add_argument("--grid-n-flow", type=int, default=32)
    parser.add_argument("--conditions", default=None,
                        help="comma-separated regime names (default: control,"
                             "neutral,lorem,adversarial). Use 'recursive' or "
                             "'recursive,no_feedback' for non-perturb experiments.")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)
    setup_logging(args.log_level, None)

    exp_dir = Path(args.data_dir) / args.experiment
    if not exp_dir.exists():
        raise FileNotFoundError(exp_dir)

    conditions = (
        [c.strip() for c in args.conditions.split(",")]
        if args.conditions else None
    )
    render_flow_skeleton_for_pilot(
        exp_dir, args.observable, args.is_dialog,
        grid_n_v=args.grid_n_v, grid_n_flow=args.grid_n_flow,
        n_basins=args.n_basins, conditions=conditions,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
