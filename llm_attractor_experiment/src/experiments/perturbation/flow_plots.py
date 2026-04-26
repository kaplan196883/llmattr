"""
Flow-field visualizations for perturbation experiments.

Four-panel PCA + four-panel t-SNE layouts — one panel per perturbation
condition — each showing the averaged displacement field in that condition's
own projection. Joint PCA/t-SNE across all conditions so they share geometry.

Key differences from src.experiments.dynamics.regime_plots:
  - No "regime == 'recursive'" filter (regime encodes condition here).
  - Separate panel per condition, not per experiment.
  - Injection-step markers overlaid so the perturbation event is visible.

Outputs per pilot (exp_dir/reports/perturbation/):
  - flow_pca_by_condition.png
  - flow_tsne_by_condition.png
  - trajectories_tsne_by_condition.png

Usage:
    python -m src.experiments.perturbation.flow_plots \\
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
from src.utils.io import ensure_dir, load_npy, read_parquet
from src.utils.logging import get_logger, setup_logging

log = get_logger(__name__)


CONDITIONS = ["control", "neutral", "lorem", "adversarial"]
COND_COLORS = {"control": "#4a90e2", "neutral": "#8b5cf6",
               "lorem": "#ff9800", "adversarial": "#d62728"}


def _load(exp_dir: Path, observable: str, is_dialog: bool) -> tuple[np.ndarray, pd.DataFrame]:
    vec_p = exp_dir / "embeddings" / observable / "embeddings.npy"
    meta_p = exp_dir / "embeddings" / observable / "metadata.parquet"
    if not vec_p.exists() or not meta_p.exists():
        raise FileNotFoundError(f"embeddings missing at {vec_p}")
    vecs = load_npy(vec_p)
    meta = read_parquet(meta_p).reset_index(drop=True)
    if is_dialog and "role" in meta.columns:
        # Pick the responder role: try "agent" (D1), then "expert" (D2);
        # else default to the alphabetically-second role (role_b convention).
        unique_roles = sorted(meta["role"].dropna().unique().tolist())
        for cand in ("agent", "expert"):
            if cand in unique_roles:
                target_role = cand
                break
        else:
            target_role = unique_roles[-1] if unique_roles else "agent"
        mask = (meta["role"] == target_role).values
        vecs = vecs[mask]
        meta = meta[mask].reset_index(drop=True)
    return vecs, meta


def _collect_starts_deltas(
    Z: np.ndarray, meta: pd.DataFrame, group_cols: list[str],
) -> tuple[np.ndarray, np.ndarray] | None:
    """Group meta by `group_cols`, sort each by step, emit (start, delta) pairs.

    Returns (S, D) of shape (M, 2) each, or None if no group has >=2 points.
    """
    starts: list[np.ndarray] = []
    deltas: list[np.ndarray] = []
    for _, sub in meta.groupby(list(group_cols)):
        sub = sub.sort_values("step")
        idx = sub.index.to_numpy()
        z_run = Z[idx]
        if len(z_run) < 2:
            continue
        starts.append(z_run[:-1])
        deltas.append(z_run[1:] - z_run[:-1])
    if not starts:
        return None
    return np.concatenate(starts, axis=0), np.concatenate(deltas, axis=0)


def _compute_flow_field(
    Z: np.ndarray, meta: pd.DataFrame, grid_n: int = 26,
    group_cols: tuple[str, ...] = ("regime", "prompt_family", "initial_condition_id", "run_id"),
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Bin (start, delta) onto grid_n x grid_n grid. Returns X, Y, U, V, density."""
    sd = _collect_starts_deltas(Z, meta, list(group_cols))
    if sd is None:
        return (np.zeros((grid_n, grid_n)),) * 5
    S, D = sd
    X, Y, x_edges, y_edges = make_grid_edges(Z, grid_n)
    U, V = bin_displacement_field(S, D, x_edges, y_edges)
    density = bin_density(Z, x_edges, y_edges)
    return X, Y, U, V, density


def _draw_injection_markers(
    ax, Z: np.ndarray, meta: pd.DataFrame, override_step: int, cond: str,
    draw_kick_arrows: bool = True, marker_color: str | None = None,
) -> None:
    """
    Overlay injection-event visualization on an existing axis.

    Finds the first step for which condition `cond` has data at or after
    override_step (handles dialog/role-filtering: if agent turns are even and
    injection is at an odd user step, effect_step becomes override_step + 1).

    For condition != 'control':
      - Arrows from each trajectory's pre-injection position (nearest step <
        effect_step with data) to its effect_step position — the "kick".
      - Big X markers at the kick-landing coordinate for each trajectory.

    For condition == 'control':
      - Small dots at the same effect_step for reference.
    """
    color = marker_color or COND_COLORS[cond]
    keys = ["prompt_family", "initial_condition_id", "run_id"]

    cond_rows = meta[meta["regime"] == cond]
    available_steps = sorted(cond_rows["step"].unique().tolist())
    if not available_steps:
        return
    # Pick the smallest available step >= override_step as the "injection effect"
    post = [s for s in available_steps if s >= override_step]
    if not post:
        return
    effect_step = int(post[0])
    # And the latest available step < effect_step as "pre-injection"
    pre = [s for s in available_steps if s < effect_step]
    prev_step = int(pre[-1]) if pre else effect_step  # edge case: no pre

    sub_prev = cond_rows[cond_rows["step"] == prev_step]
    sub_inj  = cond_rows[cond_rows["step"] == effect_step]

    if cond == "control":
        inj_idx = sub_inj.index.to_numpy()
        if len(inj_idx):
            ax.scatter(
                Z[inj_idx, 0], Z[inj_idx, 1],
                s=28, marker="o", color=color, alpha=0.7,
                edgecolors="white", linewidths=1.0, zorder=5,
                label=f"step {effect_step} positions",
            )
        return

    if draw_kick_arrows and len(sub_prev) and len(sub_inj):
        prev_sorted = sub_prev.sort_values(keys).reset_index()
        inj_sorted = sub_inj.sort_values(keys).reset_index()
        # Take only matched pairs (some runs may be missing one endpoint)
        merged = prev_sorted.merge(
            inj_sorted, on=keys, suffixes=("_p", "_i"), how="inner",
        )
        p_pos = Z[merged["index_p"].to_numpy()]
        i_pos = Z[merged["index_i"].to_numpy()]
        for a, b in zip(p_pos, i_pos):
            ax.plot(
                [a[0], b[0]], [a[1], b[1]],
                color=color, alpha=0.6, linewidth=0.6, zorder=4,
            )
            mx, my = 0.5 * (a[0] + b[0]), 0.5 * (a[1] + b[1])
            dx, dy = b[0] - a[0], b[1] - a[1]
            ax.annotate(
                "",
                xy=(mx + 0.02 * dx, my + 0.02 * dy),
                xytext=(mx - 0.02 * dx, my - 0.02 * dy),
                arrowprops=dict(
                    arrowstyle="-|>", color=color, alpha=0.9,
                    mutation_scale=10, linewidth=0,
                ),
                zorder=5,
            )

    # Small circular markers at the kick-landing coord
    inj_idx = sub_inj.index.to_numpy()
    if len(inj_idx):
        ax.scatter(
            Z[inj_idx, 0], Z[inj_idx, 1],
            s=18, marker="o", color=color,
            edgecolors="white", linewidths=0.5, zorder=6,
            label=f"step {effect_step} post-injection (N={len(inj_idx)})",
        )


def plot_flow_by_condition(
    Z: np.ndarray, meta: pd.DataFrame, override_step: int, out_path: Path,
    projection_label: str = "PCA-2", grid_n: int = 26,
) -> None:
    """Four-panel layout, one per condition, shared coords."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 14), sharex=True, sharey=True)
    x_min, x_max = float(Z[:, 0].min()), float(Z[:, 0].max())
    y_min, y_max = float(Z[:, 1].min()), float(Z[:, 1].max())
    for ax, cond in zip(axes.flat, CONDITIONS):
        idx = (meta["regime"] == cond).values
        if idx.sum() < 10:
            ax.set_title(f"{cond} (no data)")
            continue
        sub_Z = Z[idx]
        sub_meta = meta[idx].reset_index(drop=True)
        X, Y, U, V, density = _compute_flow_field(sub_Z, sub_meta, grid_n=grid_n)
        mesh = ax.pcolormesh(X, Y, np.log1p(density), cmap="Greys", alpha=0.35, shading="auto")
        mask = ~np.isnan(U) & ~np.isnan(V) & (density >= 2)
        mag = np.where(mask, np.sqrt(U**2 + V**2), np.nan)
        if mask.any():
            ax.quiver(
                X[mask], Y[mask], U[mask], V[mask],
                mag[mask], cmap="plasma",
                scale_units="xy", scale=1.0, angles="xy",
                width=0.004, alpha=0.9,
            )
        ax.scatter(sub_Z[:, 0], sub_Z[:, 1], s=2, alpha=0.15, color="k", linewidths=0)
        _draw_injection_markers(ax, Z, meta, override_step, cond)
        n_traj = int(sub_meta.groupby(
            ["prompt_family", "initial_condition_id", "run_id"]).ngroups)
        ax.set_title(f"{cond}  (N={n_traj} trajectories)", fontsize=12,
                     color=COND_COLORS[cond])
        ax.grid(alpha=0.15)
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        ax.legend(fontsize=9, loc="lower right")
    axes[1, 0].set_xlabel(f"{projection_label} dim 1")
    axes[1, 1].set_xlabel(f"{projection_label} dim 1")
    axes[0, 0].set_ylabel(f"{projection_label} dim 2")
    axes[1, 0].set_ylabel(f"{projection_label} dim 2")
    fig.suptitle(
        f"Perturbation flow field by condition ({projection_label})\n"
        f"averaged per-step displacement; arrows show step {override_step-1} → {override_step} kick caused by injection",
        fontsize=14, y=1.00,
    )
    fig.savefig(out_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def plot_trajectories_by_condition(
    Z: np.ndarray, meta: pd.DataFrame, override_step: int, out_path: Path,
    projection_label: str = "t-SNE-2",
) -> None:
    """Four-panel tSNE trajectories, one per condition, colored by step."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 14), sharex=True, sharey=True)
    x_min, x_max = float(Z[:, 0].min()), float(Z[:, 0].max())
    y_min, y_max = float(Z[:, 1].min()), float(Z[:, 1].max())
    max_step = int(meta["step"].max())
    for ax, cond in zip(axes.flat, CONDITIONS):
        idx_cond = (meta["regime"] == cond)
        sub_meta = meta[idx_cond].reset_index(drop=True)
        if sub_meta.empty:
            ax.set_title(f"{cond} (no data)")
            continue
        sub_Z = Z[idx_cond.values]
        # trajectory lines
        for _, traj in sub_meta.groupby(["prompt_family", "initial_condition_id", "run_id"]):
            traj = traj.sort_values("step")
            ixs = traj.index.to_numpy()
            ax.plot(sub_Z[ixs, 0], sub_Z[ixs, 1],
                    color="#555", alpha=0.15, lw=0.6)
        # points colored by step (dark=early, bright=late)
        ax.scatter(sub_Z[:, 0], sub_Z[:, 1],
                   c=sub_meta["step"], cmap="magma", s=7, alpha=0.6,
                   edgecolors="none")
        # injection kick (arrow from step-1 → step) + big X marker
        _draw_injection_markers(ax, Z, meta, override_step, cond)
        n_traj = sub_meta.groupby(
            ["prompt_family", "initial_condition_id", "run_id"]).ngroups
        ax.set_title(f"{cond}  (N={n_traj}, steps 0–{max_step})",
                     fontsize=12, color=COND_COLORS[cond])
        ax.grid(alpha=0.15)
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        ax.legend(fontsize=9, loc="lower right")
    axes[1, 0].set_xlabel(f"{projection_label} dim 1")
    axes[1, 1].set_xlabel(f"{projection_label} dim 1")
    axes[0, 0].set_ylabel(f"{projection_label} dim 2")
    axes[1, 0].set_ylabel(f"{projection_label} dim 2")
    fig.suptitle(
        f"Perturbation trajectories by condition ({projection_label}, colored by step)\n"
        f"injection at step {override_step}; arrows show step {override_step-1} → {override_step} kick",
        fontsize=14, y=1.00,
    )
    fig.savefig(out_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def run(exp_dir: Path, observable: str, override_step: int, is_dialog: bool) -> None:
    vecs, meta = _load(exp_dir, observable, is_dialog)
    log.info("loaded %d points for %s (observable=%s, is_dialog=%s)",
             len(vecs), exp_dir.name, observable, is_dialog)

    out_dir = exp_dir / "reports" / "perturbation"
    ensure_dir(out_dir)

    # Joint PCA-2 on ALL conditions (so coords shared across panels)
    pca = PCA(n_components=2, random_state=42)
    Z_pca = pca.fit_transform(vecs)
    log.info("PCA-2 explained variance: %.3f", float(pca.explained_variance_ratio_.sum()))
    plot_flow_by_condition(Z_pca, meta, override_step,
                           out_dir / "flow_pca_by_condition.png",
                           projection_label="PCA-2")
    log.info("wrote flow_pca_by_condition.png")

    # Joint PCA-50 pre-reduction then t-SNE-2
    pre_pca_dim = min(50, vecs.shape[1])
    Z50 = PCA(n_components=pre_pca_dim, random_state=42).fit_transform(vecs)
    perplexity = min(30, max(5, (len(Z50) - 1) // 4))
    tsne = TSNE(n_components=2, perplexity=perplexity, metric="cosine",
                random_state=42, init="pca", learning_rate="auto")
    Z_tsne = tsne.fit_transform(Z50)
    log.info("t-SNE-2 fit (perplexity=%s)", perplexity)
    plot_flow_by_condition(Z_tsne, meta, override_step,
                           out_dir / "flow_tsne_by_condition.png",
                           projection_label="t-SNE-2")
    log.info("wrote flow_tsne_by_condition.png")

    plot_trajectories_by_condition(Z_tsne, meta, override_step,
                                   out_dir / "trajectories_tsne_by_condition.png",
                                   projection_label="t-SNE-2")
    log.info("wrote trajectories_tsne_by_condition.png")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="perturbation_flow_plots")
    parser.add_argument("--experiment", required=True, help="Experiment id (dir name under data/)")
    parser.add_argument("--observable", default="context_tail")
    parser.add_argument("--override-step", type=int, default=15)
    parser.add_argument("--is-dialog", action="store_true",
                        help="Restrict to role=agent for dialog experiments")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)
    setup_logging(args.log_level, None)

    exp_dir = Path(args.data_dir) / args.experiment
    if not exp_dir.exists():
        raise FileNotFoundError(f"experiment dir not found: {exp_dir}")

    run(exp_dir, args.observable, args.override_step, args.is_dialog)
    return 0


if __name__ == "__main__":
    sys.exit(main())
