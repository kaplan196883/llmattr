"""
Holographic-RG stacking visualization for perturbation experiments.

Build a tower of progressively coarser k-means clusterings of the embedding
cloud and stack them along a radial axis z. The boundary (z=0, k=64) is fine;
the deep bulk (z=2, k=4) is coarse. Each cluster centroid is placed at the
PCA-2 location of its members' mean. Parent-child cluster pairs are connected
with edges. A subset of trajectories is rendered as 'bulk worldlines' —
at each trajectory step the point projects to one centroid per layer; the
worldline rises through layers and across (x,y) over trajectory time.

This is the holographic-RG analogue: scale-as-radial-direction. UV (small
scale, fine clustering) lives near the boundary; IR (large scale, coarse
basins) lives deep in the bulk.

Output:
  data/<exp>/reports/perturbation/rg_stack_pca.png
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
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

from src.experiments.perturbation.flow_plots import _load
from src.utils.io import ensure_dir
from src.utils.logging import get_logger, setup_logging

log = get_logger(__name__)


CONDITIONS = ["control", "neutral", "lorem", "adversarial"]
COND_COLORS = {"control": "#4a90e2", "neutral": "#8b5cf6",
               "lorem": "#ff9800", "adversarial": "#d62728"}

DPI = 220
LAYER_KS = [64, 16, 4]
LAYER_Z = [0.0, 1.0, 2.0]


def _hierarchical_kmeans(X_high: np.ndarray) -> list[np.ndarray]:
    """Return list of cluster-assignment vectors, one per layer (LAYER_KS)."""
    assignments = []
    fine = KMeans(n_clusters=LAYER_KS[0], random_state=42, n_init=8).fit(X_high)
    assignments.append(fine.labels_)
    fine_centroids = fine.cluster_centers_

    mid = KMeans(n_clusters=LAYER_KS[1], random_state=42, n_init=8).fit(fine_centroids)
    # Map fine label -> mid label; then mid label per data point
    fine_to_mid = mid.labels_
    mid_assign = fine_to_mid[fine.labels_]
    assignments.append(mid_assign)

    coarse = KMeans(n_clusters=LAYER_KS[2], random_state=42, n_init=8).fit(mid.cluster_centers_)
    mid_to_coarse = coarse.labels_
    coarse_assign = mid_to_coarse[mid_assign]
    assignments.append(coarse_assign)

    parent_maps = (None, fine_to_mid, mid_to_coarse)  # layer i -> layer i+1 mapping
    return assignments, parent_maps


def _layer_centroid_positions(Z2: np.ndarray, labels: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
    """Per-cluster (x, y) mean and population count."""
    xs, ys, ns = [], [], []
    for c in range(k):
        m = labels == c
        n = int(m.sum())
        if n == 0:
            xs.append(np.nan); ys.append(np.nan); ns.append(0); continue
        xs.append(float(Z2[m, 0].mean()))
        ys.append(float(Z2[m, 1].mean()))
        ns.append(n)
    return np.array(xs), np.array(ys), np.array(ns)


def _draw_panel(
    ax, Z2_cond: np.ndarray, meta_cond: pd.DataFrame, X_high_cond: np.ndarray,
    cond: str, max_trajs: int = 20, traj_seed: int = 0,
):
    color = COND_COLORS[cond]
    if len(X_high_cond) < LAYER_KS[0]:
        ax.set_title(f"{cond} (insufficient data)")
        return

    assignments, parent_maps = _hierarchical_kmeans(X_high_cond)

    layer_pos = []  # [(xs, ys, ns), ...]
    for i, k in enumerate(LAYER_KS):
        xs, ys, ns = _layer_centroid_positions(Z2_cond, assignments[i], k)
        layer_pos.append((xs, ys, ns))

    # Background scatter at z=-0.15 for orientation
    ax.scatter(Z2_cond[:, 0], Z2_cond[:, 1], np.full(len(Z2_cond), -0.15),
               s=1, alpha=0.06, color="#888", linewidths=0)

    # Draw each layer's centroids
    for li, (z, k) in enumerate(zip(LAYER_Z, LAYER_KS)):
        xs, ys, ns = layer_pos[li]
        sizes = 8 + 0.8 * ns / max(ns.max(), 1) * 100
        ax.scatter(xs, ys, np.full(k, z), s=sizes, alpha=0.85,
                   color=color, edgecolors="white", linewidths=0.6, zorder=10)

    # Parent-child edges
    for li in range(len(LAYER_KS) - 1):
        xs_l, ys_l, _ = layer_pos[li]
        xs_p, ys_p, _ = layer_pos[li + 1]
        pmap = parent_maps[li + 1]  # layer li -> layer li+1 mapping
        z0, z1 = LAYER_Z[li], LAYER_Z[li + 1]
        for c_idx in range(LAYER_KS[li]):
            p_idx = int(pmap[c_idx])
            if np.isnan(xs_l[c_idx]) or np.isnan(xs_p[p_idx]):
                continue
            ax.plot(
                [xs_l[c_idx], xs_p[p_idx]],
                [ys_l[c_idx], ys_p[p_idx]],
                [z0, z1],
                color=color, alpha=0.35, lw=0.7, zorder=5,
            )

    # Trajectory worldlines through layers
    rng = np.random.default_rng(traj_seed)
    keys = list(meta_cond.groupby(["prompt_family", "initial_condition_id", "run_id"]).groups.keys())
    if len(keys) > max_trajs:
        idxs = rng.choice(len(keys), size=max_trajs, replace=False)
        keys = [keys[int(i)] for i in idxs]

    for key in keys:
        m = (
            (meta_cond["prompt_family"] == key[0]) &
            (meta_cond["initial_condition_id"] == key[1]) &
            (meta_cond["run_id"] == key[2])
        )
        idxs = meta_cond.index[m].to_numpy()
        if len(idxs) < 2:
            continue
        # build worldline path: at each step, visit (cluster_pos_layer0, layer1, layer2)
        for li in range(len(LAYER_KS)):
            xs, ys, _ = layer_pos[li]
            cluster_idxs = assignments[li][idxs]
            xs_traj = xs[cluster_idxs]
            ys_traj = ys[cluster_idxs]
            zs_traj = np.full(len(idxs), LAYER_Z[li])
            ax.plot(xs_traj, ys_traj, zs_traj,
                    color=color, alpha=0.3, lw=0.6, zorder=8)

    ax.set_title(f"{cond}", fontsize=12, color=color)
    ax.set_xlabel("PCA-1", fontsize=8)
    ax.set_ylabel("PCA-2", fontsize=8)
    ax.set_zlabel("RG layer (k=64 → 16 → 4)", fontsize=8)
    ax.set_zticks(LAYER_Z)
    ax.set_zticklabels([f"k={k}" for k in LAYER_KS])
    ax.tick_params(labelsize=7)


def render_rg_for_pilot(
    exp_dir: Path, observable: str, is_dialog: bool, pre_pca_dim: int = 30,
) -> None:
    vecs, meta = _load(exp_dir, observable, is_dialog)
    log.info("loaded %d points for %s", len(vecs), exp_dir.name)

    out_dir = exp_dir / "reports" / "perturbation"
    ensure_dir(out_dir)

    # Joint PCA-2 for layout, joint PCA-30 for clustering
    Z2 = PCA(n_components=2, random_state=42).fit_transform(vecs)
    X_high = PCA(n_components=min(pre_pca_dim, vecs.shape[1]),
                 random_state=42).fit_transform(vecs)

    fig = plt.figure(figsize=(18, 14))
    for i, cond in enumerate(CONDITIONS, start=1):
        ax = fig.add_subplot(2, 2, i, projection="3d")
        sub_idx = (meta["regime"] == cond).values
        if sub_idx.sum() < LAYER_KS[0]:
            ax.set_title(f"{cond} (insufficient data)")
            continue
        Z2_cond = Z2[sub_idx]
        meta_cond = meta[sub_idx].reset_index(drop=True)
        X_high_cond = X_high[sub_idx]
        _draw_panel(ax, Z2_cond, meta_cond, X_high_cond, cond)
        ax.view_init(elev=22, azim=-56)

    fig.suptitle(
        "Holographic-RG stack: hierarchical k-means coarse-graining (PCA-2 layout)\n"
        "boundary (z=0, k=64) = fine clusters; deep bulk (z=2, k=4) = coarse basins\n"
        "centroid size ∝ population; vertical edges = parent-child mapping; "
        "lateral lines = trajectory worldlines through each layer",
        fontsize=13, y=0.995,
    )
    p = out_dir / "rg_stack_pca.png"
    fig.savefig(p, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    log.info("wrote %s", p)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="perturb_rg_stack")
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--observable", default="context_tail")
    parser.add_argument("--is-dialog", action="store_true")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)
    setup_logging(args.log_level, None)

    exp_dir = Path(args.data_dir) / args.experiment
    if not exp_dir.exists():
        raise FileNotFoundError(exp_dir)

    render_rg_for_pilot(exp_dir, args.observable, args.is_dialog)
    return 0


if __name__ == "__main__":
    sys.exit(main())
