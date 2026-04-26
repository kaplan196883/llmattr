"""
G/H/I-style field visualizations for perturbation experiments, in a 4-panel
per-condition layout (one panel each for control/neutral/lorem/adversarial).

Mirrors src.experiments.dynamics.field_plots but:
  - Uses a joint PCA-2 / t-SNE-2 projection across ALL conditions so panels
    share geometry.
  - Computes per-condition flow field separately so per-panel streamlines
    show that condition's dynamics.
  - Marks injection points with X markers.

Outputs per pilot (exp_dir/reports/perturbation/):
  G_streamlines_density_by_condition_{pca,tsne}.png
  H_speed_streamlines_by_condition_{pca,tsne}.png
  I_divergence_by_condition_{pca,tsne}.png

Usage:
    python -m src.experiments.perturbation.field_plots \
        --experiment exp_perturb_D1_pilot --observable context_tail --is-dialog
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
from sklearn.manifold import TSNE

from src.experiments.dynamics._grid_utils import (
    bin_density, bin_displacement_field, make_grid_edges,
)
from src.experiments.dynamics.field_plots import (
    _clean_uv_for_streamplot, _smooth_density_grid,
)
from src.experiments.perturbation.flow_plots import (
    _collect_starts_deltas, _compute_flow_field, _draw_injection_markers, _load,
)
from src.utils.io import ensure_dir
from src.utils.logging import get_logger, setup_logging

log = get_logger(__name__)


DPI = 300
FIG_SIZE = (18, 14)   # total figure for 2x2
CONDITIONS = ["control", "neutral", "lorem", "adversarial"]
COND_COLORS = {"control": "#4a90e2", "neutral": "#8b5cf6",
               "lorem": "#ff9800", "adversarial": "#d62728"}


def _compute_per_condition_fields(
    Z: np.ndarray, meta: pd.DataFrame, grid_n: int,
    conditions: list[str] | None = None,
) -> dict[str, tuple]:
    """Return {condition: (X, Y, U, V, density, pts)} with shared grid bounds."""
    if conditions is None:
        conditions = CONDITIONS
    # Shared grid across all conditions, derived from the full point cloud.
    Xg, Yg, x_edges, y_edges = make_grid_edges(Z, grid_n)

    out = {}
    for cond in conditions:
        idx = (meta["regime"] == cond).values
        if idx.sum() < 10:
            out[cond] = None
            continue
        sub_Z = Z[idx]
        sub_meta = meta[idx].reset_index(drop=True)
        sd = _collect_starts_deltas(
            sub_Z, sub_meta, ["prompt_family", "initial_condition_id", "run_id"],
        )
        if sd is None:
            out[cond] = None
            continue
        S, D = sd
        U, V = bin_displacement_field(S, D, x_edges, y_edges)
        density = bin_density(sub_Z, x_edges, y_edges)
        out[cond] = (Xg, Yg, U, V, density, sub_Z)
    return out


def _plot_panel_streamlines_density(
    ax, result: tuple, cond: str, xbounds, ybounds, override_step: int,
    Z_all: np.ndarray, meta_all: pd.DataFrame,
) -> None:
    X, Y, U, V, density, pts = result
    U2, V2 = _clean_uv_for_streamplot(X, Y, U, V, density)
    Xd, Yd, Hs = _smooth_density_grid(
        pts, xbounds, ybounds, grid_n=96, sigma_cells=1.8,
    )
    ax.pcolormesh(Xd, Yd, np.log1p(Hs), cmap="magma", alpha=0.9, shading="gouraud")
    if (np.sqrt(U2**2 + V2**2) > 0).sum() > 10:
        ax.streamplot(
            X, Y, U2, V2,
            color="white", linewidth=0.9, density=1.8, arrowsize=1.0,
            arrowstyle="-|>",
        )
    ax.scatter(pts[:, 0], pts[:, 1], s=0.5, alpha=0.1, color="#ccc", linewidths=0)
    _draw_injection_markers(ax, Z_all, meta_all, override_step, cond)
    ax.set_title(f"{cond}", fontsize=12, color=COND_COLORS[cond])
    ax.set_xlim(xbounds); ax.set_ylim(ybounds)
    ax.grid(alpha=0.1, color="#555")
    ax.legend(fontsize=8, loc="lower right")


def _plot_panel_speed_streamlines(
    ax, result: tuple, cond: str, xbounds, ybounds,
    Z_all: np.ndarray, meta_all: pd.DataFrame, fig,
) -> None:
    X, Y, U, V, density, pts = result
    U2, V2 = _clean_uv_for_streamplot(X, Y, U, V, density)
    mag = np.sqrt(U2**2 + V2**2)
    ax.set_facecolor("#0a0a0a")
    if (mag > 0).sum() > 10:
        strm = ax.streamplot(
            X, Y, U2, V2,
            color=mag, cmap="plasma", linewidth=1.2, density=2.0,
            arrowsize=1.2, arrowstyle="-|>",
        )
    ax.scatter(pts[:, 0], pts[:, 1], s=0.6, alpha=0.1, color="#666", linewidths=0)
    _draw_injection_markers(ax, Z_all, meta_all, 15, cond)  # override_step default 15
    ax.set_title(f"{cond}", fontsize=12, color=COND_COLORS[cond])
    ax.set_xlim(xbounds); ax.set_ylim(ybounds)
    for spine in ax.spines.values():
        spine.set_color("#aaa")
    ax.tick_params(colors="#bbb")
    ax.grid(alpha=0.1, color="#333")


def _plot_panel_divergence(
    ax, result: tuple, cond: str, xbounds, ybounds,
    Z_all: np.ndarray, meta_all: pd.DataFrame, override_step: int,
    vmax_global: float | None = None,
) -> None:
    X, Y, U, V, density, pts = result
    U2, V2 = _clean_uv_for_streamplot(X, Y, U, V, density)
    dx = X[0, 1] - X[0, 0]
    dy = Y[1, 0] - Y[0, 0]
    dUdx = np.gradient(U2, dx, axis=1)
    dVdy = np.gradient(V2, dy, axis=0)
    div = dUdx + dVdy
    mask = density >= 2
    div_m = np.where(mask, div, np.nan)
    finite = div_m[np.isfinite(div_m)]
    vmax = vmax_global or (
        float(np.nanpercentile(np.abs(finite), 98)) if finite.size else 1.0
    )
    ax.pcolormesh(X, Y, div_m, cmap="RdBu_r", vmin=-vmax, vmax=vmax, shading="auto")
    if (np.sqrt(U2**2 + V2**2) > 0).sum() > 10:
        ax.streamplot(
            X, Y, U2, V2, color="black", linewidth=0.5, density=1.2,
            arrowsize=0.8, arrowstyle="-|>",
        )
    _draw_injection_markers(ax, Z_all, meta_all, override_step, cond)
    ax.set_title(f"{cond}  (vmax={vmax:.3f})", fontsize=12, color=COND_COLORS[cond])
    ax.set_xlim(xbounds); ax.set_ylim(ybounds)
    ax.grid(alpha=0.15)


def render_fields_for_pilot(
    exp_dir: Path, observable: str, override_step: int,
    is_dialog: bool, grid_n_pca: int = 32, grid_n_tsne: int = 32,
    skip_tsne: bool = False,
) -> None:
    vecs, meta = _load(exp_dir, observable, is_dialog)
    log.info("loaded %d points for %s (is_dialog=%s)",
             len(vecs), exp_dir.name, is_dialog)

    out_dir = exp_dir / "reports" / "perturbation"
    ensure_dir(out_dir)

    # ---- Joint PCA-2 ----
    pca2 = PCA(n_components=2, random_state=42).fit_transform(vecs)
    log.info("joint PCA-2 computed")
    _render_all_three(pca2, meta, override_step, out_dir, observable,
                      tag="pca", grid_n=grid_n_pca)

    if skip_tsne:
        return

    # ---- Joint t-SNE-2 ----
    pre_pca_dim = min(50, vecs.shape[1])
    Z50 = PCA(n_components=pre_pca_dim, random_state=42).fit_transform(vecs)
    perp = min(30, max(5, (len(Z50) - 1) // 4))
    tsne2 = TSNE(
        n_components=2, perplexity=perp, metric="cosine",
        random_state=42, init="pca", learning_rate="auto",
    ).fit_transform(Z50)
    log.info("joint t-SNE-2 computed (perplexity=%s)", perp)
    _render_all_three(tsne2, meta, override_step, out_dir, observable,
                      tag="tsne", grid_n=grid_n_tsne)


def _render_all_three(
    Z: np.ndarray, meta: pd.DataFrame, override_step: int, out_dir: Path,
    observable: str, tag: str, grid_n: int,
) -> None:
    fields = _compute_per_condition_fields(Z, meta, grid_n=grid_n)
    x_min, x_max = float(Z[:, 0].min()), float(Z[:, 0].max())
    y_min, y_max = float(Z[:, 1].min()), float(Z[:, 1].max())
    xpad = 0.05 * (x_max - x_min + 1e-9)
    ypad = 0.05 * (y_max - y_min + 1e-9)
    xb = (x_min - xpad, x_max + xpad)
    yb = (y_min - ypad, y_max + ypad)

    space_label = "PCA-2" if tag == "pca" else "PCA-50 → t-SNE-2"

    # ---- G: streamlines + density ----
    fig, axes = plt.subplots(2, 2, figsize=FIG_SIZE, sharex=True, sharey=True)
    for ax, cond in zip(axes.flat, CONDITIONS):
        r = fields.get(cond)
        if r is None:
            ax.set_title(f"{cond} (no data)")
            continue
        _plot_panel_streamlines_density(ax, r, cond, xb, yb, override_step, Z, meta)
    axes[1, 0].set_xlabel(f"{space_label} 1")
    axes[1, 1].set_xlabel(f"{space_label} 1")
    axes[0, 0].set_ylabel(f"{space_label} 2")
    axes[1, 0].set_ylabel(f"{space_label} 2")
    fig.suptitle(
        f"G: streamlines + smoothed density by condition ({space_label})\n"
        f"injection at step {override_step}  |  "
        "white streamlines = flow direction; magma = trajectory-visit density",
        fontsize=14, y=1.00,
    )
    p = out_dir / f"G_streamlines_density_by_condition_{tag}.png"
    fig.savefig(p, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    log.info("wrote %s", p)

    # ---- H: speed-colored streamlines (dark background) ----
    fig, axes = plt.subplots(2, 2, figsize=FIG_SIZE, sharex=True, sharey=True,
                             facecolor="#0a0a0a")
    for ax, cond in zip(axes.flat, CONDITIONS):
        r = fields.get(cond)
        if r is None:
            ax.set_title(f"{cond} (no data)")
            continue
        _plot_panel_speed_streamlines(ax, r, cond, xb, yb, Z, meta, fig)
    for ax in axes.flat:
        ax.xaxis.label.set_color("#ddd")
        ax.yaxis.label.set_color("#ddd")
    axes[1, 0].set_xlabel(f"{space_label} 1", color="#ddd")
    axes[1, 1].set_xlabel(f"{space_label} 1", color="#ddd")
    axes[0, 0].set_ylabel(f"{space_label} 2", color="#ddd")
    axes[1, 0].set_ylabel(f"{space_label} 2", color="#ddd")
    fig.suptitle(
        f"H: speed-colored streamlines by condition ({space_label})\n"
        f"injection at step {override_step}  |  cold = slow (basin interior); warm = fast transport",
        fontsize=14, y=1.00, color="#eee",
    )
    p = out_dir / f"H_speed_streamlines_by_condition_{tag}.png"
    fig.savefig(p, dpi=DPI, bbox_inches="tight", facecolor="#0a0a0a")
    plt.close(fig)
    log.info("wrote %s", p)

    # ---- I: divergence heatmap ----
    # For comparable color scale, use global vmax across conditions
    div_maxes = []
    for r in fields.values():
        if r is None: continue
        _, _, U, V, density, _ = r
        U2, V2 = _clean_uv_for_streamplot(_, _, U, V, density)
        dx = r[0][0, 1] - r[0][0, 0]
        dy = r[1][1, 0] - r[1][0, 0]
        dUdx = np.gradient(U2, dx, axis=1)
        dVdy = np.gradient(V2, dy, axis=0)
        div = dUdx + dVdy
        mask = density >= 2
        div_m = np.where(mask, div, np.nan)
        f = div_m[np.isfinite(div_m)]
        if f.size:
            div_maxes.append(float(np.nanpercentile(np.abs(f), 98)))
    vmax_g = max(div_maxes) if div_maxes else 1.0

    fig, axes = plt.subplots(2, 2, figsize=FIG_SIZE, sharex=True, sharey=True)
    for ax, cond in zip(axes.flat, CONDITIONS):
        r = fields.get(cond)
        if r is None:
            ax.set_title(f"{cond} (no data)")
            continue
        _plot_panel_divergence(ax, r, cond, xb, yb, Z, meta, override_step, vmax_global=vmax_g)
    axes[1, 0].set_xlabel(f"{space_label} 1")
    axes[1, 1].set_xlabel(f"{space_label} 1")
    axes[0, 0].set_ylabel(f"{space_label} 2")
    axes[1, 0].set_ylabel(f"{space_label} 2")
    fig.suptitle(
        f"I: divergence field ∇·v by condition ({space_label})\n"
        f"injection at step {override_step}  |  blue = sink / attractor; red = source / repeller  (shared scale)",
        fontsize=14, y=1.00,
    )
    p = out_dir / f"I_divergence_by_condition_{tag}.png"
    fig.savefig(p, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    log.info("wrote %s", p)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="perturb_field_plots")
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--observable", default="context_tail")
    parser.add_argument("--override-step", type=int, default=15)
    parser.add_argument("--is-dialog", action="store_true")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--grid-n-pca", type=int, default=32)
    parser.add_argument("--grid-n-tsne", type=int, default=32)
    parser.add_argument("--skip-tsne", action="store_true")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)
    setup_logging(args.log_level, None)

    exp_dir = Path(args.data_dir) / args.experiment
    if not exp_dir.exists():
        raise FileNotFoundError(exp_dir)

    render_fields_for_pilot(
        exp_dir, args.observable, args.override_step, args.is_dialog,
        grid_n_pca=args.grid_n_pca, grid_n_tsne=args.grid_n_tsne,
        skip_tsne=args.skip_tsne,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
