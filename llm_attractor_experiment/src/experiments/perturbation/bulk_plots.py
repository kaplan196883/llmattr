"""
Free-energy / 'holographic-bulk' visualization for perturbation experiments.

For a perturbation experiment with conditions {control, neutral, lorem,
adversarial}, render a 4-panel 3D figure where each panel is the effective
potential V(x) = -log ρ(x) of one condition's trajectory cloud, computed in
the joint PCA-2 projection so panels share geometry. Trajectories are drawn
as 3D paths riding the surface (height interpolated from V at each step).

Reading:
  - Wells = attractor basins.
  - Cliff edges = barriers between basins.
  - The kick (injection) is a near-instantaneous lateral hop in (x, y);
    the height jump tracks how 'far up' the perturbation pushed the
    trajectory before relaxation.

This is borrowed visual language from holographic-bulk reasoning, not a
literal AdS/CFT duality. V is the boundary-distribution-derived static
landscape; trajectories are the boundary observers' worldlines on it.

Output (per experiment):
  data/<exp>/reports/perturbation/bulk_landscape_pca.png
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
from scipy.interpolate import RegularGridInterpolator
from sklearn.decomposition import PCA

from src.experiments.dynamics.field_plots import _smooth_density_grid
from src.experiments.perturbation.flow_plots import _load
from src.utils.io import ensure_dir
from src.utils.logging import get_logger, setup_logging

log = get_logger(__name__)


CONDITIONS = ["control", "neutral", "lorem", "adversarial"]
COND_COLORS = {"control": "#4a90e2", "neutral": "#8b5cf6",
               "lorem": "#ff9800", "adversarial": "#d62728"}

DPI = 220


def _potential_grid(
    pts: np.ndarray,
    xbounds: tuple[float, float],
    ybounds: tuple[float, float],
    grid_n: int = 64,
    sigma_cells: float = 2.0,
    v_cap: float = 6.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (X, Y, V) where V = -log(ρ + ε), normalized so V_min=0, capped at v_cap."""
    X, Y, H = _smooth_density_grid(pts, xbounds, ybounds, grid_n=grid_n, sigma_cells=sigma_cells)
    rho = H / max(H.sum(), 1.0)
    eps = max(rho[rho > 0].min(), 1e-9) * 0.1 if (rho > 0).any() else 1e-9
    V = -np.log(rho + eps)
    V = V - V.min()
    V = np.minimum(V, v_cap)
    return X, Y, V


def _trajectory_height(traj_xy: np.ndarray, X: np.ndarray, Y: np.ndarray, V: np.ndarray) -> np.ndarray:
    """Bilinearly interpolate V at each (x,y) of a trajectory."""
    x_c = X[0, :]
    y_c = Y[:, 0]
    interp = RegularGridInterpolator((y_c, x_c), V, bounds_error=False, fill_value=V.max())
    return interp(np.column_stack([traj_xy[:, 1], traj_xy[:, 0]]))


def _draw_panel(
    ax, X, Y, V, traj_groups, override_step, cond, lift=0.15,
    max_trajs=24, traj_seed=0,
):
    surf = ax.plot_surface(
        X, Y, V, cmap="viridis", alpha=0.85, edgecolor="none",
        rstride=1, cstride=1, linewidth=0, antialiased=True,
    )
    # Sample a subset of trajectories for overlay
    rng = np.random.default_rng(traj_seed)
    keys = list(traj_groups.keys())
    if len(keys) > max_trajs:
        idxs = rng.choice(len(keys), size=max_trajs, replace=False)
        keys = [keys[int(i)] for i in idxs]
    pcolor = COND_COLORS.get(cond, "#5fa85f")
    for k in keys:
        traj_xy, steps = traj_groups[k]
        if len(traj_xy) < 2:
            continue
        z = _trajectory_height(traj_xy, X, Y, V) + lift
        ax.plot(traj_xy[:, 0], traj_xy[:, 1], z,
                color=pcolor, alpha=0.55, lw=0.8, zorder=10)
        # Mark injection effect-step with a small sphere
        post = [(i, s) for i, s in enumerate(steps) if s >= override_step]
        if post:
            i_eff, _ = post[0]
            ax.scatter(
                [traj_xy[i_eff, 0]], [traj_xy[i_eff, 1]], [z[i_eff] + 0.1],
                color=pcolor, edgecolors="white", linewidths=0.4,
                s=14, zorder=12,
            )
    ax.set_title(f"{cond}", fontsize=12, color=pcolor)
    ax.set_xlabel("PCA-1", fontsize=8)
    ax.set_ylabel("PCA-2", fontsize=8)
    ax.set_zlabel("V = -log ρ", fontsize=8)
    ax.tick_params(labelsize=7)


def _trajectory_groups(Z: np.ndarray, meta: pd.DataFrame,
                       conditions: list[str]) -> dict[str, dict]:
    """Per-condition: {(family, ic, run): (trajectory_xy, steps_array)}."""
    out = {c: {} for c in conditions}
    for cond in conditions:
        sub = meta[meta["regime"] == cond]
        for key, grp in sub.groupby(["prompt_family", "initial_condition_id", "run_id"]):
            grp = grp.sort_values("step")
            idx = grp.index.to_numpy()
            out[cond][key] = (Z[idx], grp["step"].to_numpy())
    return out


def render_bulk_for_pilot(
    exp_dir: Path, observable: str, override_step: int, is_dialog: bool,
    grid_n: int = 64, v_cap: float = 6.0,
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

    traj_groups = _trajectory_groups(Z, meta, conditions)

    n = len(conditions)
    if n <= 2:
        n_rows, n_cols = 1, n
    elif n <= 4:
        n_rows, n_cols = 2, 2
    else:
        n_cols = 3
        n_rows = (n + n_cols - 1) // n_cols
    fig = plt.figure(figsize=(9 * n_cols, 6.5 * n_rows))
    for i, cond in enumerate(conditions, start=1):
        ax = fig.add_subplot(n_rows, n_cols, i, projection="3d")
        sub_idx = (meta["regime"] == cond).values
        if sub_idx.sum() < 10:
            ax.set_title(f"{cond} (no data)")
            continue
        pts = Z[sub_idx]
        X, Y, V = _potential_grid(pts, xb, yb, grid_n=grid_n, v_cap=v_cap)
        _draw_panel(ax, X, Y, V, traj_groups[cond], override_step, cond)
        ax.view_init(elev=32, azim=-58)
        ax.set_xlim(xb); ax.set_ylim(yb); ax.set_zlim(0, v_cap)

    fig.suptitle(
        f"Free-energy 'bulk' landscape  V(x) = −log ρ(x)  by condition  (PCA-2)\n"
        f"injection at step {override_step}  |  wells = attractor basins; "
        "cliffs = inter-basin barriers; trajectory paths ride the surface",
        fontsize=14, y=0.995,
    )
    p = out_dir / "bulk_landscape_pca.png"
    fig.savefig(p, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    log.info("wrote %s", p)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="perturb_bulk_plots")
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--observable", default="context_tail")
    parser.add_argument("--override-step", type=int, default=15)
    parser.add_argument("--is-dialog", action="store_true")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--grid-n", type=int, default=64)
    parser.add_argument("--v-cap", type=float, default=6.0)
    parser.add_argument("--conditions", default=None,
                        help="comma-separated regime names (default: 4 perturb conds)")
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
    render_bulk_for_pilot(
        exp_dir, args.observable, args.override_step, args.is_dialog,
        grid_n=args.grid_n, v_cap=args.v_cap, conditions=conditions,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
