"""
Geodesic-skeleton visualization for perturbation experiments.
See ARTICLE.md §4.10 / §5.10 for the spec.

Build an effective potential V(x) = -log ρ(x) on a smoothed density grid
(joint PCA-2). Identify basin centers as local density maxima. Compute
shortest paths through the V landscape (Dijkstra over the grid graph,
with edge weights = V at endpoint) — these are the 'geodesics' / minimum-
action paths between basins. Annotate each geodesic with the maximum V
reached along it (the barrier height).

This is the dynamical-systems analogue of bulk-geodesic skeletons:
basins are extrema, geodesics are minimum-action arcs, and the maximum
of V along each arc is the saddle / barrier height.

Output:
  data/<exp>/reports/perturbation/geodesic_skeleton_pca.png
"""
from __future__ import annotations

import argparse
import heapq
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.ndimage import maximum_filter
from sklearn.decomposition import PCA

from src.experiments.dynamics.field_plots import _potential_grid, _smooth_density_grid  # noqa: F401  (re-export for flow_skeleton)
from src.experiments.perturbation.flow_plots import _load
from src.utils.io import ensure_dir
from src.utils.logging import get_logger, setup_logging

log = get_logger(__name__)


CONDITIONS = ["control", "neutral", "lorem", "adversarial"]
COND_COLORS = {"control": "#4a90e2", "neutral": "#8b5cf6",
               "lorem": "#ff9800", "adversarial": "#d62728"}

DPI = 220


def _find_basin_centers(V: np.ndarray, n_max: int = 4, neigh: int = 8) -> list[tuple[int, int]]:
    """Local minima of V (i.e., density peaks). Returns (row, col) indices."""
    local_min = V == -maximum_filter(-V, size=neigh)
    rs, cs = np.where(local_min)
    vals = V[rs, cs]
    order = np.argsort(vals)
    centers = []
    used = np.zeros_like(V, dtype=bool)
    min_dist = max(neigh // 2, 3)
    for k in order:
        r, c = int(rs[k]), int(cs[k])
        # de-duplicate: skip if too close to an already-chosen center
        ok = True
        for (r0, c0) in centers:
            if abs(r - r0) < min_dist and abs(c - c0) < min_dist:
                ok = False; break
        if ok:
            centers.append((r, c))
            if len(centers) >= n_max:
                break
    return centers


def _grid_dijkstra(
    V: np.ndarray, src: tuple[int, int], dst: tuple[int, int],
) -> list[tuple[int, int]]:
    """Shortest path on the grid; edge weight = V at endpoint."""
    H, W = V.shape
    dist = np.full((H, W), np.inf)
    prev = -np.ones((H, W, 2), dtype=np.int32)
    dist[src] = 0.0
    heap = [(0.0, src[0], src[1])]
    while heap:
        d, r, c = heapq.heappop(heap)
        if (r, c) == dst:
            break
        if d > dist[r, c]:
            continue
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1),
                       (-1, -1), (-1, 1), (1, -1), (1, 1)]:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < H and 0 <= nc < W):
                continue
            step = float(V[nr, nc]) * (1.4142 if dr and dc else 1.0)
            nd = d + step
            if nd < dist[nr, nc]:
                dist[nr, nc] = nd
                prev[nr, nc] = (r, c)
                heapq.heappush(heap, (nd, nr, nc))
    # Reconstruct
    if not np.isfinite(dist[dst]):
        return []
    path = [dst]
    while path[-1] != src:
        r, c = path[-1]
        pr, pc = prev[r, c]
        if pr < 0:
            break
        path.append((int(pr), int(pc)))
    return list(reversed(path))


def _draw_panel(
    ax, X, Y, V, pts, cond: str, n_basins: int = 4,
) -> list[dict]:
    """Render one condition panel and return per-geodesic barrier records.

    Each record: {condition, basin_i, basin_j, basin_i_x, basin_i_y,
    basin_j_x, basin_j_y, V_star, n_basins}.
    """
    color = COND_COLORS.get(cond, "#5fa85f")
    cs = ax.contourf(X, Y, V, levels=20, cmap="magma", alpha=0.55)
    ax.contour(X, Y, V, levels=10, colors="#555", linewidths=0.4, alpha=0.5)
    ax.scatter(pts[:, 0], pts[:, 1], s=0.4, alpha=0.10, color="#222", linewidths=0)

    centers = _find_basin_centers(V, n_max=n_basins)
    if not centers:
        ax.set_title(f"{cond} (no basins found)", fontsize=11)
        return []

    # Plot basin centers
    for (r, c) in centers:
        ax.scatter(X[r, c], Y[r, c], s=120, marker="*", color=color,
                   edgecolors="black", linewidths=1.0, zorder=10)

    # Compute pairwise geodesics for the top n basins
    records: list[dict] = []
    n_centers = len(centers)
    for i in range(n_centers):
        for j in range(i + 1, n_centers):
            path = _grid_dijkstra(V, centers[i], centers[j])
            if not path:
                continue
            xs = np.array([X[r, c] for r, c in path])
            ys = np.array([Y[r, c] for r, c in path])
            v_path = np.array([V[r, c] for r, c in path])
            v_max = float(v_path.max())
            ri, ci = centers[i]
            rj, cj = centers[j]
            records.append({
                "condition": cond,
                "basin_i": i,
                "basin_j": j,
                "basin_i_x": float(X[ri, ci]),
                "basin_i_y": float(Y[ri, ci]),
                "basin_j_x": float(X[rj, cj]),
                "basin_j_y": float(Y[rj, cj]),
                "V_star": v_max,
                "n_basins": n_centers,
            })
            ax.plot(xs, ys, color=color, lw=1.3, alpha=0.85, zorder=8)
            mid = len(path) // 2
            ax.annotate(
                f"V*={v_max:.1f}",
                xy=(xs[mid], ys[mid]),
                xytext=(6, 6), textcoords="offset points",
                fontsize=8, color=color,
                bbox=dict(boxstyle="round,pad=0.2",
                          fc="white", ec=color, alpha=0.85, lw=0.6),
                zorder=12,
            )

    ax.set_title(f"{cond}  ({n_centers} basins, "
                 f"{len(records)} geodesics)",
                 fontsize=11, color=color)
    ax.set_xlabel("PCA-1")
    ax.set_ylabel("PCA-2")
    return records


def render_geodesic_for_pilot(
    exp_dir: Path, observable: str, is_dialog: bool,
    grid_n: int = 96, n_basins: int = 4,
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
    all_records: list[dict] = []
    for ax, cond in zip(axes.flat, conditions):
        sub_idx = (meta["regime"] == cond).values
        if sub_idx.sum() < 30:
            ax.set_title(f"{cond} (no data)")
            continue
        pts = Z[sub_idx]
        X, Y, V = _potential_grid(pts, xb, yb, grid_n=grid_n)
        recs = _draw_panel(ax, X, Y, V, pts, cond, n_basins=n_basins)
        all_records.extend(recs)
        ax.set_xlim(xb); ax.set_ylim(yb)
        ax.grid(alpha=0.15)
    for ax in axes.flat[n:]:
        ax.set_visible(False)

    fig.suptitle(
        "Geodesic skeleton: minimum-action paths between basin density-peaks (PCA-2)\n"
        "★ = basin center (local density maximum)  |  curves = Dijkstra geodesics on V grid  "
        "|  V* = max-V along path (barrier height)",
        fontsize=13, y=1.00,
    )
    p = out_dir / "geodesic_skeleton_pca.png"
    fig.savefig(p, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    log.info("wrote %s", p)

    # Per-geodesic barriers CSV (companion to the PNG; see ARTICLE.md §5.10).
    barriers_csv = out_dir / "geodesic_barriers_pca.csv"
    barriers_df = pd.DataFrame(all_records, columns=[
        "condition", "basin_i", "basin_j",
        "basin_i_x", "basin_i_y", "basin_j_x", "basin_j_y",
        "V_star", "n_basins",
    ])
    barriers_df.to_csv(barriers_csv, index=False)
    log.info("wrote %s (%d rows)", barriers_csv, len(barriers_df))

    # Per-condition summary (mean / min / max V* across geodesics).
    summary_csv = out_dir / "geodesic_barriers_summary.csv"
    if len(barriers_df):
        summary = (
            barriers_df.groupby("condition")
            .agg(
                n_basins=("n_basins", "first"),
                n_geodesics=("V_star", "size"),
                V_star_mean=("V_star", "mean"),
                V_star_min=("V_star", "min"),
                V_star_max=("V_star", "max"),
            )
            .reset_index()
        )
    else:
        summary = pd.DataFrame(columns=[
            "condition", "n_basins", "n_geodesics",
            "V_star_mean", "V_star_min", "V_star_max",
        ])
    summary.to_csv(summary_csv, index=False)
    log.info("wrote %s (%d rows)", summary_csv, len(summary))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="perturb_geodesic_skeleton")
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--observable", default="context_tail")
    parser.add_argument("--is-dialog", action="store_true")
    parser.add_argument("--n-basins", type=int, default=4)
    parser.add_argument("--conditions", default=None,
                        help="comma-separated regime names (default: 4 perturb conds)")
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
    render_geodesic_for_pilot(exp_dir, args.observable, args.is_dialog,
                              n_basins=args.n_basins, conditions=conditions)
    return 0


if __name__ == "__main__":
    sys.exit(main())
