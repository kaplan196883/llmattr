"""
Hierarchical-RG dendrogram visualization for perturbation experiments.
See ARTICLE.md §4.11.6 / §5.10 for the spec.

Per condition:
  1. K-means at k=64 on PCA-30 → 64 leaf "fine basins" with populations.
  2. scipy Ward linkage on the 64 centroids → hierarchical merge tree.
  3. Render as a horizontal dendrogram. The y-axis is Ward linkage distance,
     which is the coarse-graining scale: leaves (right) = fine; root (left) =
     coarsest grouping.

This is a coarse-graining picture borrowed from renormalization-group
intuition: trajectory clouds at different scales are layers; merge events
are coarse-graining steps.

Output:
  data/<exp>/reports/perturbation/rg_dendrogram_pca.png
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
from scipy.cluster.hierarchy import dendrogram, linkage
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
# K = 48 KMeans + Ward linkage. The article narrative in §5.10 (lorem
# collapses the cloud under replace-mode) is computed at K=48; switching
# to K=64 inverts the sign of the lorem-vs-control effect for O2/O3
# because higher leaf counts isolate small outlier clusters that pull
# the maximum merge distance up. Article and code agree at K=48.
N_LEAVES = 48
PRE_PCA = 30


def _build_linkage(X: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Returns (linkage_matrix, leaf_centroids, leaf_populations)."""
    if len(X) < N_LEAVES:
        n_leaves = max(2, len(X) // 4)
    else:
        n_leaves = N_LEAVES
    km = KMeans(n_clusters=n_leaves, random_state=42, n_init=8).fit(X)
    centroids = km.cluster_centers_
    pops = np.bincount(km.labels_, minlength=n_leaves).astype(int)
    Z = linkage(centroids, method="ward")
    return Z, centroids, pops


def _draw_panel(ax, Z, pops, cond) -> dict:
    """Render one condition panel and return a summary record.

    Record fields: {condition, n_leaves, total_points, max_merge_distance,
    mean_merge_distance, median_merge_distance}.
    """
    color = COND_COLORS.get(cond, "#5fa85f")
    n = len(pops)
    # Width labels: pop counts
    labels = [f"{int(p)}" for p in pops]

    # Render dendrogram horizontally, color all branches by condition color
    ddata = dendrogram(
        Z, ax=ax, orientation="left", labels=labels,
        color_threshold=0,  # all branches one color via link_color_func
        link_color_func=lambda _: color,
        leaf_font_size=6,
    )

    # Annotate the linkage scale at the root
    merge_d = Z[:, 2]
    max_d = float(merge_d.max())
    ax.set_xlim(0, max_d * 1.05)
    ax.set_xlabel("Ward linkage distance (RG scale)", fontsize=9)
    ax.set_ylabel("fine cluster (label = population)", fontsize=9)
    ax.set_title(f"{cond}  (n_leaves={n}, total pts={int(pops.sum())}, "
                 f"max merge dist={max_d:.2f})",
                 fontsize=11, color=color)
    ax.tick_params(labelsize=7)
    ax.grid(axis="x", alpha=0.25)
    return {
        "condition": cond,
        "n_leaves": int(n),
        "total_points": int(pops.sum()),
        "max_merge_distance": max_d,
        "mean_merge_distance": float(merge_d.mean()),
        "median_merge_distance": float(np.median(merge_d)),
    }


def render_dendrogram_for_pilot(
    exp_dir: Path, observable: str, is_dialog: bool,
    conditions: list[str] | None = None,
) -> None:
    vecs, meta = _load(exp_dir, observable, is_dialog)
    log.info("loaded %d points for %s", len(vecs), exp_dir.name)

    out_dir = exp_dir / "reports" / "perturbation"
    ensure_dir(out_dir)

    if conditions is None:
        conditions = CONDITIONS

    # Joint PCA-30 across all conditions for a fair embedding metric
    X_high = PCA(n_components=min(PRE_PCA, vecs.shape[1]),
                 random_state=42).fit_transform(vecs)

    n = len(conditions)
    if n <= 2:
        n_rows, n_cols = 1, n
    elif n <= 4:
        n_rows, n_cols = 2, 2
    else:
        n_cols = 3
        n_rows = (n + n_cols - 1) // n_cols
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(9 * n_cols, 7 * n_rows),
                             squeeze=False)
    summary_rows: list[dict] = []
    for ax, cond in zip(axes.flat, conditions):
        sub_idx = (meta["regime"] == cond).values
        if sub_idx.sum() < 50:
            ax.set_title(f"{cond} (no data)")
            continue
        Xc = X_high[sub_idx]
        Z_link, centroids, pops = _build_linkage(Xc)
        rec = _draw_panel(ax, Z_link, pops, cond)
        summary_rows.append(rec)
    for ax in axes.flat[n:]:
        ax.set_visible(False)

    fig.suptitle(
        "Hierarchical dendrogram: Ward linkage of fine-cluster centroids per condition (PCA-30)\n"
        "horizontal axis = RG scale (linkage distance)  |  leaves = fine basins; "
        "root = single coarse cluster\n"
        "branch geometry encodes how trajectory mass coarsens across scales",
        fontsize=13, y=1.00,
    )
    p = out_dir / "rg_dendrogram_pca.png"
    fig.savefig(p, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    log.info("wrote %s", p)

    # Per-condition summary CSV (companion to the PNG; see ARTICLE.md §5.10).
    summary_csv = out_dir / "rg_dendrogram_summary.csv"
    summary_df = pd.DataFrame(summary_rows, columns=[
        "condition", "n_leaves", "total_points",
        "max_merge_distance", "mean_merge_distance", "median_merge_distance",
    ])
    summary_df.to_csv(summary_csv, index=False)
    log.info("wrote %s (%d rows)", summary_csv, len(summary_df))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="perturb_rg_dendrogram")
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--observable", default="context_tail")
    parser.add_argument("--is-dialog", action="store_true")
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
    render_dendrogram_for_pilot(exp_dir, args.observable, args.is_dialog,
                                conditions=conditions)
    return 0


if __name__ == "__main__":
    sys.exit(main())
