"""
t-SNE visualizations for the in-flight O1_pub partial snapshot.

Reads cached embeddings from data/<exp>/partial_analysis/embeddings_rolling_k3.npy
(written by partial_snapshot.py). No API calls; purely post-hoc.

Output: data/<exp>/partial_analysis/plots/
  ├── joint_tsne_by_family.png
  ├── joint_tsne_by_step.png
  └── tsne_trajectories_<family>.png  (one per family with enough data)
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

from src.config import load_config
from src.utils.io import ensure_dir, load_npy
from src.utils.logging import get_logger, setup_logging

log = get_logger(__name__)


def _fit_tsne(
    X: np.ndarray, pre_pca: int = 50, perplexity: float = 40.0, seed: int = 42
) -> np.ndarray:
    k = min(pre_pca, X.shape[1], len(X) - 1)
    if X.shape[1] > k and k >= 2:
        X = PCA(n_components=k, random_state=seed).fit_transform(X)
    perp = min(perplexity, max(5.0, (len(X) - 1) / 4))
    return TSNE(
        n_components=2,
        perplexity=perp,
        init="pca",
        learning_rate="auto",
        metric="cosine",
        random_state=seed,
    ).fit_transform(X)


def plot_joint_by_family(Z: np.ndarray, meta: pd.DataFrame, out_dir: Path, exp_id: str) -> Path:
    families = sorted(meta["prompt_family"].unique())
    cmap = plt.get_cmap("tab20", max(1, len(families)))
    fig, ax = plt.subplots(figsize=(12, 8))
    for i, fam in enumerate(families):
        mask = meta["prompt_family"].values == fam
        ax.scatter(
            Z[mask, 0],
            Z[mask, 1],
            s=4,
            alpha=0.55,
            color=cmap(i % cmap.N),
            label=f"{fam}  (n={mask.sum()})",
            linewidths=0,
        )
    ax.set_title(
        f"{exp_id} partial — joint t-SNE of recursive rolling_k3 embeddings, "
        f"colored by prompt family\n"
        f"{len(Z)} points across {len(families)} families; pre-PCA-50 → t-SNE-2 (cosine)"
    )
    ax.set_xlabel("t-SNE 1")
    ax.set_ylabel("t-SNE 2")
    ax.legend(loc="best", fontsize=8, markerscale=2.5)
    ax.grid(alpha=0.2)
    ensure_dir(out_dir)
    p = out_dir / "joint_tsne_by_family.png"
    fig.savefig(p, dpi=140, bbox_inches="tight")
    plt.close(fig)
    log.info("wrote %s", p)
    return p


def plot_joint_by_step(Z: np.ndarray, meta: pd.DataFrame, out_dir: Path, exp_id: str) -> Path:
    fig, ax = plt.subplots(figsize=(11, 8))
    sc = ax.scatter(
        Z[:, 0],
        Z[:, 1],
        c=meta["step"].values,
        s=4,
        alpha=0.55,
        cmap="viridis",
        linewidths=0,
    )
    cbar = fig.colorbar(sc, ax=ax, pad=0.02, label="step within trajectory")
    cbar.ax.tick_params(labelsize=9)
    ax.set_title(
        f"{exp_id} partial — joint t-SNE, time-colored\n"
        f"are late-time points clustered or spread?"
    )
    ax.set_xlabel("t-SNE 1")
    ax.set_ylabel("t-SNE 2")
    ax.grid(alpha=0.2)
    ensure_dir(out_dir)
    p = out_dir / "joint_tsne_by_step.png"
    fig.savefig(p, dpi=140, bbox_inches="tight")
    plt.close(fig)
    log.info("wrote %s", p)
    return p


def plot_family_trajectories(
    Z: np.ndarray,
    meta: pd.DataFrame,
    family: str,
    out_dir: Path,
    exp_id: str,
    max_traces: int = 40,
) -> Path | None:
    fam_mask = meta["prompt_family"].values == family
    if fam_mask.sum() < 30:
        return None
    meta_fam = meta[fam_mask].reset_index(drop=True)
    Z_fam = Z[fam_mask]

    # Re-fit t-SNE on this family's embeddings only so local structure dominates
    # (this gives a cleaner per-family picture than cropping the joint t-SNE)
    fig, ax = plt.subplots(figsize=(10, 8))
    cmap = plt.get_cmap("viridis")
    ax.scatter(Z_fam[:, 0], Z_fam[:, 1], s=4, alpha=0.12, color="k", linewidths=0)
    traced = 0
    for _keys, sub in meta_fam.groupby(
        ["prompt_family", "initial_condition_id", "run_id"]
    ):
        if traced >= max_traces:
            break
        sub_sorted = sub.sort_values("step")
        idx = sub_sorted.index.to_numpy()
        z_run = Z_fam[idx]
        if len(z_run) < 2:
            continue
        T = len(z_run)
        for t in range(T - 1):
            c = cmap(t / max(1, T - 1))
            ax.annotate(
                "",
                xy=(z_run[t + 1, 0], z_run[t + 1, 1]),
                xytext=(z_run[t, 0], z_run[t, 1]),
                arrowprops=dict(
                    arrowstyle="->",
                    color=c,
                    alpha=0.5,
                    linewidth=0.8,
                    shrinkA=0,
                    shrinkB=0,
                ),
            )
        ax.scatter(
            z_run[0, 0], z_run[0, 1],
            s=30, facecolors="none", edgecolors="red", linewidths=1.1, zorder=3,
        )
        traced += 1

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=0, vmax=1))
    sm.set_array([])
    fig.colorbar(sm, ax=ax, pad=0.02, label="step (normalized)")
    ax.set_title(
        f"{exp_id} partial — t-SNE trajectories for family '{family}'\n"
        f"{traced} runs drawn (out of {len(meta_fam.groupby(['prompt_family','initial_condition_id','run_id']))}); "
        f"red circles = step 0 / seed"
    )
    ax.set_xlabel("t-SNE 1 (family-local)")
    ax.set_ylabel("t-SNE 2 (family-local)")
    ax.grid(alpha=0.2)
    ensure_dir(out_dir)
    p = out_dir / f"tsne_trajectories_{family}.png"
    fig.savefig(p, dpi=140, bbox_inches="tight")
    plt.close(fig)
    log.info("wrote %s", p)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="partial_tsne")
    parser.add_argument("--config", required=True)
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)
    setup_logging(args.log_level, None)
    cfg = load_config(args.config)

    pa_dir = cfg.experiment_dir / "partial_analysis"
    emb_path = pa_dir / "embeddings_rolling_k3.npy"
    meta_path = pa_dir / "metadata_rolling_k3.parquet"
    if not emb_path.exists() or not meta_path.exists():
        log.error("no cached partial embeddings; run partial_snapshot first")
        return 1

    vecs = load_npy(emb_path)
    meta = pd.read_parquet(meta_path)
    log.info("loaded %d embeddings for %s", len(vecs), cfg.experiment_id)

    # Joint t-SNE across all recursive rolling_k3 points
    log.info("fitting joint t-SNE on %d points", len(vecs))
    Z_joint = _fit_tsne(vecs)
    out_dir = pa_dir / "plots"
    plot_joint_by_family(Z_joint, meta, out_dir, cfg.experiment_id)
    plot_joint_by_step(Z_joint, meta, out_dir, cfg.experiment_id)

    # Per-family trajectory plots (only families with enough data)
    # For these, re-fit t-SNE on the family subset so local structure dominates
    for fam in sorted(meta["prompt_family"].unique()):
        fam_mask = meta["prompt_family"].values == fam
        n = int(fam_mask.sum())
        if n < 30:
            log.info("skipping family '%s' (n=%d, too few points)", fam, n)
            continue
        fam_vecs = vecs[fam_mask]
        meta_fam_reset = meta[fam_mask].reset_index(drop=True)
        log.info("fitting family-local t-SNE for '%s' on %d points", fam, n)
        Z_fam = _fit_tsne(fam_vecs)
        # Create a synthetic global Z for plot_family_trajectories, but it only
        # uses the fam subset so we can pass Z_fam directly by putting it back.
        _plot_family_trajectories_local(
            Z_fam, meta_fam_reset, fam, out_dir, cfg.experiment_id
        )

    return 0


def _plot_family_trajectories_local(
    Z: np.ndarray,
    meta: pd.DataFrame,
    family: str,
    out_dir: Path,
    exp_id: str,
    max_traces: int = 60,
) -> Path:
    """Per-family trajectory plot using a family-local t-SNE fit."""
    fig, ax = plt.subplots(figsize=(10, 8))
    cmap = plt.get_cmap("viridis")
    ax.scatter(Z[:, 0], Z[:, 1], s=4, alpha=0.12, color="k", linewidths=0)
    traced = 0
    traj_groups = list(meta.groupby(["prompt_family", "initial_condition_id", "run_id"]))
    for _keys, sub in traj_groups:
        if traced >= max_traces:
            break
        sub_sorted = sub.sort_values("step")
        idx = sub_sorted.index.to_numpy()
        z_run = Z[idx]
        if len(z_run) < 2:
            continue
        T = len(z_run)
        for t in range(T - 1):
            c = cmap(t / max(1, T - 1))
            ax.annotate(
                "",
                xy=(z_run[t + 1, 0], z_run[t + 1, 1]),
                xytext=(z_run[t, 0], z_run[t, 1]),
                arrowprops=dict(
                    arrowstyle="->",
                    color=c,
                    alpha=0.4,
                    linewidth=0.7,
                    shrinkA=0,
                    shrinkB=0,
                ),
            )
        ax.scatter(
            z_run[0, 0], z_run[0, 1],
            s=28, facecolors="none", edgecolors="red", linewidths=1.0, zorder=3,
        )
        traced += 1

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=0, vmax=1))
    sm.set_array([])
    fig.colorbar(sm, ax=ax, pad=0.02, label="step (normalized)")
    ax.set_title(
        f"{exp_id} partial — t-SNE trajectories for family '{family}'\n"
        f"{traced} of {len(traj_groups)} runs drawn  "
        f"(family-local t-SNE fit; red circles = seed at step 0)"
    )
    ax.set_xlabel("t-SNE 1 (family-local)")
    ax.set_ylabel("t-SNE 2 (family-local)")
    ax.grid(alpha=0.2)
    ensure_dir(out_dir)
    p = out_dir / f"tsne_trajectories_{family}.png"
    fig.savefig(p, dpi=140, bbox_inches="tight")
    plt.close(fig)
    log.info("wrote %s", p)
    return p


if __name__ == "__main__":
    sys.exit(main())
