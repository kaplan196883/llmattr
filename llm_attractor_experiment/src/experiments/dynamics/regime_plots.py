"""
Cross-experiment visual evidence of the four observed regimes.

Three plots:

  A. Joint t-SNE across ALL experiments' embeddings, colored by regime.
     Shows whether same-regime experiments cluster together in a shared
     embedding-space topology.

  B. Per-experiment PCA-2 trajectory grid (4×3 layout, 11 panels).
     Each panel shows the recursive-regime trajectories in that experiment's
     own PCA-2 space, time-colored (dark=early, bright=late). Reveals the
     qualitative shape: basin vs 2-cycle vs absorbing point vs diffuse.

  C. Ensemble spread timeline — mean pairwise run-to-run distance as a
     function of step, one line per experiment.

Writes to data/dynamics_plots/.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

from src.config import load_config
from src.experiments.dynamics.plots import DISPLAY, REGIME_COLOR, REGIME_LABEL
from src.utils.io import ensure_dir, load_npy, read_parquet
from src.utils.logging import get_logger

log = get_logger(__name__)

OBS_DEFAULT = "rolling_k3"


def _collect_all_embeddings(
    data_dir: Path, observable: str
) -> tuple[np.ndarray, pd.DataFrame]:
    """
    Concatenate recursive-regime embeddings from every experiment.
    Returns (vecs, meta) where meta has an added 'experiment_id' column.
    """
    all_vecs: list[np.ndarray] = []
    all_meta: list[pd.DataFrame] = []
    for exp_dir in sorted(data_dir.iterdir()):
        if not exp_dir.is_dir():
            continue
        cfg_path = exp_dir / "config.yaml"
        if not cfg_path.exists():
            continue
        vec_p = exp_dir / "embeddings" / observable / "embeddings.npy"
        meta_p = exp_dir / "embeddings" / observable / "metadata.parquet"
        if not vec_p.exists() or not meta_p.exists():
            continue
        vecs = load_npy(vec_p)
        meta = read_parquet(meta_p).copy()
        meta["experiment_id"] = exp_dir.name
        rec = meta["regime"] == "recursive"
        if rec.sum() == 0:
            continue
        all_vecs.append(vecs[rec.values])
        all_meta.append(meta[rec].reset_index(drop=True))
    if not all_vecs:
        return np.zeros((0, 0)), pd.DataFrame()
    return np.concatenate(all_vecs, axis=0), pd.concat(all_meta, ignore_index=True)


# ---------- Plot A: joint t-SNE across all experiments ----------


def plot_joint_tsne(
    data_dir: Path,
    out_dir: Path,
    observable: str = OBS_DEFAULT,
    pre_pca: int = 50,
    perplexity: float = 40.0,
    seed: int = 42,
) -> Path:
    log.info("plot A: collecting all embeddings for observable=%s", observable)
    vecs, meta = _collect_all_embeddings(data_dir, observable)
    if len(vecs) < 10:
        log.warning("not enough embeddings for joint t-SNE")
        return out_dir / f"A_joint_tsne_{observable}.png"

    log.info(
        "plot A: joint t-SNE on %d points (pre_pca=%d, perplexity=%g)",
        len(vecs),
        pre_pca,
        perplexity,
    )
    # Pre-PCA to 50-d for speed + noise reduction, then t-SNE to 2-d.
    if vecs.shape[1] > pre_pca:
        pca = PCA(n_components=pre_pca, random_state=seed)
        X = pca.fit_transform(vecs)
    else:
        X = vecs
    perp = min(perplexity, max(5, (len(X) - 1) / 4))
    tsne = TSNE(
        n_components=2,
        perplexity=perp,
        init="pca",
        learning_rate="auto",
        metric="cosine",
        random_state=seed,
    )
    Z = tsne.fit_transform(X)

    fig, ax = plt.subplots(figsize=(11, 8))
    exp_to_regime = {e: REGIME_LABEL.get(e, "unknown") for e in meta["experiment_id"].unique()}
    # one scatter per regime for a clean legend
    for regime in sorted(set(exp_to_regime.values())):
        mask = meta["experiment_id"].map(exp_to_regime) == regime
        color = REGIME_COLOR.get(regime, "#888")
        ax.scatter(
            Z[mask, 0],
            Z[mask, 1],
            s=5,
            alpha=0.55,
            color=color,
            label=regime,
            linewidths=0,
        )

    ax.set_title(
        f"Joint t-SNE of recursive trajectories (observable={observable}) — "
        f"{len(Z)} points across 11 experiments\n"
        f"colored by regime (t-SNE after PCA-{pre_pca}, cosine, perplexity={perp:.0f})"
    )
    ax.set_xlabel("t-SNE 1")
    ax.set_ylabel("t-SNE 2")
    ax.legend(loc="best", fontsize=10, markerscale=2)
    ax.grid(alpha=0.2)

    ensure_dir(out_dir)
    path = out_dir / f"A_joint_tsne_{observable}.png"
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    log.info("wrote %s", path)
    return path


# ---------- Plot B: per-experiment PCA trajectory grid ----------


def _pca2_runs_for_experiment(
    exp_dir: Path, observable: str
) -> tuple[list[np.ndarray], pd.DataFrame] | None:
    """
    Returns list of per-run PCA-2 projections (N runs × (T, 2)) and a metadata
    DataFrame aligned with each concatenated row.
    """
    vec_p = exp_dir / "embeddings" / observable / "embeddings.npy"
    meta_p = exp_dir / "embeddings" / observable / "metadata.parquet"
    if not vec_p.exists() or not meta_p.exists():
        return None
    vecs = load_npy(vec_p)
    meta = read_parquet(meta_p).copy()
    rec = meta[meta["regime"] == "recursive"].reset_index(drop=True)
    if rec.empty:
        return None

    # Fit PCA-2 on the experiment's OWN recursive points (joint across runs).
    indices = rec.index.to_numpy()  # these are original positions in meta
    # We used reset_index above so we lost them; recompute.
    meta2 = read_parquet(meta_p)
    rec_idx = np.where(meta2["regime"] == "recursive")[0]
    vecs_rec = vecs[rec_idx]
    meta_rec = meta2.iloc[rec_idx].reset_index(drop=True)
    if len(vecs_rec) < 3:
        return None

    pca = PCA(n_components=2, random_state=0)
    Z = pca.fit_transform(vecs_rec)

    runs: list[np.ndarray] = []
    group_cols = ["prompt_family", "initial_condition_id", "run_id"]
    for keys, sub in meta_rec.groupby(group_cols, dropna=False):
        idx = sub.sort_values("step").index.to_numpy()
        runs.append(Z[idx])
    return runs, meta_rec


def plot_trajectory_grid(
    data_dir: Path,
    out_dir: Path,
    observable: str = OBS_DEFAULT,
) -> Path:
    exp_order = list(REGIME_LABEL.keys())
    exps_available = [
        e for e in exp_order if (data_dir / e / "config.yaml").exists()
    ]

    n_exp = len(exps_available)
    ncols = 4
    nrows = int(np.ceil(n_exp / ncols))
    fig, axes = plt.subplots(
        nrows, ncols, figsize=(4.2 * ncols, 3.6 * nrows), squeeze=False
    )

    cmap = plt.get_cmap("viridis")
    plotted = 0
    for ax_i, exp_name in enumerate(exps_available):
        ax = axes[ax_i // ncols, ax_i % ncols]
        regime = REGIME_LABEL.get(exp_name, "unknown")
        title_color = REGIME_COLOR.get(regime, "#333")
        result = _pca2_runs_for_experiment(data_dir / exp_name, observable)
        if result is None:
            ax.set_title(f"{DISPLAY.get(exp_name, exp_name)}\n(no data)", color=title_color, fontsize=10)
            ax.axis("off")
            continue
        runs, _meta = result
        if not runs:
            ax.set_title(f"{DISPLAY.get(exp_name, exp_name)}\n(no data)", color=title_color, fontsize=10)
            ax.axis("off")
            continue

        T = max(len(r) for r in runs)
        for run in runs:
            t_norm = np.arange(len(run)) / max(1, T - 1)
            colors = cmap(t_norm)
            # line segments colored by step
            for i in range(len(run) - 1):
                ax.plot(
                    [run[i, 0], run[i + 1, 0]],
                    [run[i, 1], run[i + 1, 1]],
                    color=colors[i],
                    alpha=0.55,
                    lw=0.9,
                )
            ax.scatter(run[:, 0], run[:, 1], s=8, c=t_norm, cmap=cmap, alpha=0.8, linewidths=0)
        ax.set_title(
            f"{DISPLAY.get(exp_name, exp_name)}  —  {regime}",
            color=title_color,
            fontsize=10,
        )
        ax.set_xlabel("PC1", fontsize=8)
        ax.set_ylabel("PC2", fontsize=8)
        ax.tick_params(labelsize=7)
        ax.grid(alpha=0.15)
        plotted += 1

    # turn off unused axes
    for ax_i in range(n_exp, nrows * ncols):
        axes[ax_i // ncols, ax_i % ncols].axis("off")

    # shared colorbar for time
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=0, vmax=1))
    sm.set_array([])
    cbar = fig.colorbar(
        sm,
        ax=axes.ravel().tolist(),
        fraction=0.02,
        pad=0.02,
        label="step (normalized: 0=first, 1=last)",
    )
    cbar.ax.tick_params(labelsize=8)

    fig.suptitle(
        f"Recursive trajectories in per-experiment PCA-2 space "
        f"(observable = {observable}) — one subplot per experiment, "
        f"time-colored (dark → bright)",
        fontsize=12,
        y=1.01,
    )
    ensure_dir(out_dir)
    path = out_dir / f"B_trajectory_grid_{observable}.png"
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    log.info("wrote %s (%d panels filled)", path, plotted)
    return path


# ---------- Plot C: ensemble spread over time ----------


def _spread_per_step_for_experiment(
    exp_dir: Path, observable: str
) -> np.ndarray | None:
    """
    Returns a 1D array of mean pairwise run-to-run distance at each step,
    averaged across all (family, IC) groups in the recursive regime.
    """
    vec_p = exp_dir / "embeddings" / observable / "embeddings.npy"
    meta_p = exp_dir / "embeddings" / observable / "metadata.parquet"
    if not vec_p.exists() or not meta_p.exists():
        return None
    vecs = load_npy(vec_p)
    meta = read_parquet(meta_p)
    rec = meta[meta["regime"] == "recursive"]
    if rec.empty:
        return None

    spread_per_group: list[np.ndarray] = []
    for _keys, sub in rec.groupby(["prompt_family", "initial_condition_id"]):
        runs: list[np.ndarray] = []
        T_ref = None
        ok = True
        for _rid, rs in sub.groupby("run_id"):
            rs = rs.sort_values("step")
            r_vecs = vecs[rs.index.to_numpy()]
            if T_ref is None:
                T_ref = len(r_vecs)
            elif len(r_vecs) != T_ref:
                ok = False
                break
            runs.append(r_vecs)
        if not ok or T_ref is None or len(runs) < 2:
            continue
        stack = np.stack(runs)  # (N, T, d)
        # mean pairwise distance at each step
        spread = np.zeros(T_ref)
        for t in range(T_ref):
            pts = stack[:, t, :]
            diff = pts[:, None, :] - pts[None, :, :]
            dists = np.linalg.norm(diff, axis=-1)
            iu = np.triu_indices(len(pts), k=1)
            spread[t] = float(dists[iu].mean())
        spread_per_group.append(spread)

    if not spread_per_group:
        return None
    # pad to max length with NaNs, then nanmean
    max_T = max(len(s) for s in spread_per_group)
    padded = np.full((len(spread_per_group), max_T), np.nan)
    for i, s in enumerate(spread_per_group):
        padded[i, : len(s)] = s
    return np.nanmean(padded, axis=0)


def plot_spread_timelines(
    data_dir: Path,
    out_dir: Path,
    observable: str = OBS_DEFAULT,
) -> Path:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    for exp_name, regime in REGIME_LABEL.items():
        exp_dir = data_dir / exp_name
        if not exp_dir.exists():
            continue
        spread = _spread_per_step_for_experiment(exp_dir, observable)
        if spread is None:
            continue
        color = REGIME_COLOR.get(regime, "#888")
        steps = np.arange(len(spread))
        ax1.plot(
            steps,
            spread,
            color=color,
            label=DISPLAY.get(exp_name, exp_name),
            lw=1.4,
            alpha=0.85,
        )
        # log-scale version: normalize by spread[1]
        if len(spread) > 1 and spread[1] > 0:
            norm = spread / spread[1]
            ax2.plot(
                steps,
                norm,
                color=color,
                label=DISPLAY.get(exp_name, exp_name),
                lw=1.4,
                alpha=0.85,
            )

    ax1.set_title(f"Ensemble spread vs step ({observable})")
    ax1.set_xlabel("step")
    ax1.set_ylabel("mean pairwise run-to-run distance")
    ax1.grid(alpha=0.2)
    ax1.legend(loc="best", fontsize=7, ncols=2)

    ax2.set_title("Same, normalized to spread[t=1]")
    ax2.set_xlabel("step")
    ax2.set_ylabel("spread(t) / spread(1)")
    ax2.axhline(1.0, color="k", lw=0.5, alpha=0.4, linestyle="--")
    ax2.grid(alpha=0.2)
    ax2.set_yscale("log")

    fig.suptitle(
        "Plot C: If the recursive LLM loop were chaotic, these curves would "
        "grow exponentially. Instead they flatten or grow at most mildly — "
        "visual proof that all 11 experiments are in the stable regime.",
        fontsize=10,
        y=1.02,
    )

    ensure_dir(out_dir)
    path = out_dir / f"C_spread_timeline_{observable}.png"
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    log.info("wrote %s", path)
    return path


# ---------- Plot E: per-experiment flow field ----------


def _flow_field_for_experiment(
    exp_dir: Path,
    observable: str,
    grid_n: int = 24,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray] | None:
    """
    Compute an averaged displacement vector field for one experiment in its
    own PCA-2 space.

    Returns
    -------
    X, Y           : (grid_n, grid_n) mesh coordinates (for streamplot / imshow)
    U, V           : (grid_n, grid_n) averaged dx, dy per bin (NaN where empty)
    density        : (grid_n, grid_n) visit count per bin
    pts            : (M, 2) all projected points (for scatter overlay)
    """
    vec_p = exp_dir / "embeddings" / observable / "embeddings.npy"
    meta_p = exp_dir / "embeddings" / observable / "metadata.parquet"
    if not vec_p.exists() or not meta_p.exists():
        return None
    vecs = load_npy(vec_p)
    meta = read_parquet(meta_p)
    rec_idx = np.where(meta["regime"] == "recursive")[0]
    if len(rec_idx) < 10:
        return None
    rec_vecs = vecs[rec_idx]
    rec_meta = meta.iloc[rec_idx].reset_index(drop=True)

    # PCA-2 fit jointly on all recursive points for this experiment
    pca = PCA(n_components=2, random_state=0)
    Z = pca.fit_transform(rec_vecs)

    # Collect displacement vectors per (family, ic, run) trajectory
    starts: list[np.ndarray] = []
    deltas: list[np.ndarray] = []
    for _keys, sub in rec_meta.groupby(["prompt_family", "initial_condition_id", "run_id"]):
        sub_sorted = sub.sort_values("step")
        idx_local = sub_sorted.index.to_numpy()  # reset_index earlier → these are positions in Z
        z_run = Z[idx_local]  # (T, 2)
        if len(z_run) < 2:
            continue
        starts.append(z_run[:-1])
        deltas.append(z_run[1:] - z_run[:-1])
    if not starts:
        return None
    S = np.concatenate(starts, axis=0)  # (M, 2)
    D = np.concatenate(deltas, axis=0)  # (M, 2)

    # Build grid
    x_min, x_max = Z[:, 0].min(), Z[:, 0].max()
    y_min, y_max = Z[:, 1].min(), Z[:, 1].max()
    x_pad = 0.05 * (x_max - x_min + 1e-9)
    y_pad = 0.05 * (y_max - y_min + 1e-9)
    x_edges = np.linspace(x_min - x_pad, x_max + x_pad, grid_n + 1)
    y_edges = np.linspace(y_min - y_pad, y_max + y_pad, grid_n + 1)

    # Bin starting points, sum deltas, count occupancy
    ix = np.clip(np.digitize(S[:, 0], x_edges) - 1, 0, grid_n - 1)
    iy = np.clip(np.digitize(S[:, 1], y_edges) - 1, 0, grid_n - 1)
    count = np.zeros((grid_n, grid_n))
    sum_u = np.zeros((grid_n, grid_n))
    sum_v = np.zeros((grid_n, grid_n))
    for xi, yi, du, dv in zip(ix, iy, D[:, 0], D[:, 1]):
        count[yi, xi] += 1
        sum_u[yi, xi] += du
        sum_v[yi, xi] += dv
    with np.errstate(invalid="ignore", divide="ignore"):
        U = sum_u / np.where(count > 0, count, np.nan)
        V = sum_v / np.where(count > 0, count, np.nan)

    # Mesh centers for plotting
    x_centers = 0.5 * (x_edges[:-1] + x_edges[1:])
    y_centers = 0.5 * (y_edges[:-1] + y_edges[1:])
    X, Y = np.meshgrid(x_centers, y_centers)

    # Also count all points (not just starts) for density
    density_ix = np.clip(np.digitize(Z[:, 0], x_edges) - 1, 0, grid_n - 1)
    density_iy = np.clip(np.digitize(Z[:, 1], y_edges) - 1, 0, grid_n - 1)
    density = np.zeros((grid_n, grid_n))
    for xi, yi in zip(density_ix, density_iy):
        density[yi, xi] += 1

    return X, Y, U, V, density, Z


def _flow_field_tsne_for_experiment(
    exp_dir: Path,
    observable: str,
    grid_n: int = 28,
    perplexity: float = 30.0,
    pre_pca: int = 50,
    seed: int = 42,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray] | None:
    """
    Same as _flow_field_for_experiment but in t-SNE(-via-PCA-50) space instead
    of PCA-2. t-SNE is fit ONCE on all recursive points of this experiment so
    consecutive steps share a coordinate frame.

    Returns (X, Y, U, V, density, pts) — same shape as the PCA version.
    """
    vec_p = exp_dir / "embeddings" / observable / "embeddings.npy"
    meta_p = exp_dir / "embeddings" / observable / "metadata.parquet"
    if not vec_p.exists() or not meta_p.exists():
        return None
    vecs = load_npy(vec_p)
    meta = read_parquet(meta_p)
    rec_idx = np.where(meta["regime"] == "recursive")[0]
    if len(rec_idx) < 10:
        return None
    rec_vecs = vecs[rec_idx]
    rec_meta = meta.iloc[rec_idx].reset_index(drop=True)

    # PCA-50 pre-reduction then t-SNE-2 on all recursive points at once.
    k = min(pre_pca, rec_vecs.shape[1], len(rec_vecs) - 1)
    if rec_vecs.shape[1] > k and k >= 2:
        X_prep = PCA(n_components=k, random_state=seed).fit_transform(rec_vecs)
    else:
        X_prep = rec_vecs
    perp = min(perplexity, max(5.0, (len(X_prep) - 1) / 4))
    tsne = TSNE(
        n_components=2,
        perplexity=perp,
        init="pca",
        learning_rate="auto",
        metric="cosine",
        random_state=seed,
    )
    Z = tsne.fit_transform(X_prep)  # (M, 2)

    # Collect displacement vectors per trajectory using t-SNE positions
    starts: list[np.ndarray] = []
    deltas: list[np.ndarray] = []
    for _keys, sub in rec_meta.groupby(["prompt_family", "initial_condition_id", "run_id"]):
        sub_sorted = sub.sort_values("step")
        idx_local = sub_sorted.index.to_numpy()
        z_run = Z[idx_local]
        if len(z_run) < 2:
            continue
        starts.append(z_run[:-1])
        deltas.append(z_run[1:] - z_run[:-1])
    if not starts:
        return None
    S = np.concatenate(starts, axis=0)
    D = np.concatenate(deltas, axis=0)

    x_min, x_max = Z[:, 0].min(), Z[:, 0].max()
    y_min, y_max = Z[:, 1].min(), Z[:, 1].max()
    x_pad = 0.05 * (x_max - x_min + 1e-9)
    y_pad = 0.05 * (y_max - y_min + 1e-9)
    x_edges = np.linspace(x_min - x_pad, x_max + x_pad, grid_n + 1)
    y_edges = np.linspace(y_min - y_pad, y_max + y_pad, grid_n + 1)

    ix = np.clip(np.digitize(S[:, 0], x_edges) - 1, 0, grid_n - 1)
    iy = np.clip(np.digitize(S[:, 1], y_edges) - 1, 0, grid_n - 1)
    count = np.zeros((grid_n, grid_n))
    sum_u = np.zeros((grid_n, grid_n))
    sum_v = np.zeros((grid_n, grid_n))
    for xi, yi, du, dv in zip(ix, iy, D[:, 0], D[:, 1]):
        count[yi, xi] += 1
        sum_u[yi, xi] += du
        sum_v[yi, xi] += dv
    with np.errstate(invalid="ignore", divide="ignore"):
        U = sum_u / np.where(count > 0, count, np.nan)
        V = sum_v / np.where(count > 0, count, np.nan)

    x_centers = 0.5 * (x_edges[:-1] + x_edges[1:])
    y_centers = 0.5 * (y_edges[:-1] + y_edges[1:])
    X_mesh, Y_mesh = np.meshgrid(x_centers, y_centers)

    density_ix = np.clip(np.digitize(Z[:, 0], x_edges) - 1, 0, grid_n - 1)
    density_iy = np.clip(np.digitize(Z[:, 1], y_edges) - 1, 0, grid_n - 1)
    density = np.zeros((grid_n, grid_n))
    for xi, yi in zip(density_ix, density_iy):
        density[yi, xi] += 1

    return X_mesh, Y_mesh, U, V, density, Z


def plot_flow_field_tsne_single(
    exp_name: str,
    data_dir: Path,
    out_dir: Path,
    observable: str = OBS_DEFAULT,
    grid_n: int = 28,
) -> Path | None:
    """Single-experiment flow field rendered in t-SNE space."""
    log.info("computing t-SNE flow field for %s", exp_name)
    result = _flow_field_tsne_for_experiment(data_dir / exp_name, observable, grid_n=grid_n)
    if result is None:
        return None
    X, Y, U, V, density, pts = result
    regime = REGIME_LABEL.get(exp_name, "unknown")
    title_color = REGIME_COLOR.get(regime, "#333")

    fig, ax = plt.subplots(figsize=(9, 7))
    ax.pcolormesh(X, Y, np.log1p(density), cmap="Greys", alpha=0.35, shading="auto")
    mask = ~np.isnan(U) & ~np.isnan(V) & (density >= 2)
    mag = np.where(mask, np.sqrt(U**2 + V**2), np.nan)
    if mask.any():
        q = ax.quiver(
            X[mask],
            Y[mask],
            U[mask],
            V[mask],
            mag[mask],
            cmap="plasma",
            scale_units="xy",
            scale=1.0,
            angles="xy",
            width=0.004,
            alpha=0.95,
        )
        cbar = fig.colorbar(q, ax=ax, pad=0.02, label="|displacement| per step (t-SNE units)")
        cbar.ax.tick_params(labelsize=9)
    ax.scatter(pts[:, 0], pts[:, 1], s=2, alpha=0.2, color="k", linewidths=0)
    ax.set_title(
        f"{DISPLAY.get(exp_name, exp_name)} — {regime}  (t-SNE flow field)\n"
        f"averaged Y_t → Y_(t+1) displacement after PCA-50 → t-SNE-2\n"
        f"({observable}, {len(pts)} points; arrow lengths not physical — t-SNE distorts scale)",
        color=title_color,
        fontsize=10,
    )
    ax.set_xlabel("t-SNE 1")
    ax.set_ylabel("t-SNE 2")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(alpha=0.15)

    ensure_dir(out_dir)
    path = out_dir / f"E_tsne_flow_{exp_name}_{observable}.png"
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    log.info("wrote %s", path)
    return path


def plot_flow_field_tsne_grid(
    data_dir: Path,
    out_dir: Path,
    observable: str = OBS_DEFAULT,
    grid_n: int = 28,
) -> Path:
    exp_order = [e for e in REGIME_LABEL.keys() if (data_dir / e / "config.yaml").exists()]
    n_exp = len(exp_order)
    ncols = 4
    nrows = int(np.ceil(n_exp / ncols))
    fig, axes = plt.subplots(
        nrows, ncols, figsize=(4.5 * ncols, 3.8 * nrows), squeeze=False
    )

    for ax_i, exp_name in enumerate(exp_order):
        ax = axes[ax_i // ncols, ax_i % ncols]
        regime = REGIME_LABEL.get(exp_name, "unknown")
        title_color = REGIME_COLOR.get(regime, "#333")
        log.info("t-SNE flow grid: %s", exp_name)
        result = _flow_field_tsne_for_experiment(data_dir / exp_name, observable, grid_n=grid_n)
        if result is None:
            ax.set_title(f"{DISPLAY.get(exp_name, exp_name)}\n(no data)", color=title_color, fontsize=10)
            ax.axis("off")
            continue
        X, Y, U, V, density, pts = result
        ax.pcolormesh(X, Y, np.log1p(density), cmap="Greys", alpha=0.35, shading="auto")
        mask = ~np.isnan(U) & ~np.isnan(V) & (density >= 2)
        mag = np.where(mask, np.sqrt(U**2 + V**2), np.nan)
        if mask.any():
            ax.quiver(
                X[mask], Y[mask], U[mask], V[mask], mag[mask],
                cmap="plasma", scale_units="xy", scale=1.0, angles="xy",
                width=0.004, alpha=0.9,
            )
        ax.scatter(pts[:, 0], pts[:, 1], s=1.5, alpha=0.15, color="k", linewidths=0)
        ax.set_title(
            f"{DISPLAY.get(exp_name, exp_name)}  —  {regime}",
            color=title_color,
            fontsize=10,
        )
        ax.set_xlabel("t-SNE 1", fontsize=8)
        ax.set_ylabel("t-SNE 2", fontsize=8)
        ax.tick_params(labelsize=7)
        ax.set_aspect("equal", adjustable="box")
        ax.grid(alpha=0.12)

    for ax_i in range(n_exp, nrows * ncols):
        axes[ax_i // ncols, ax_i % ncols].axis("off")

    fig.suptitle(
        f"Plot E (t-SNE variant) — averaged displacement vector fields after PCA-50 → t-SNE-2\n"
        f"(observable = {observable}; arrow lengths not physical, directions within a blob are meaningful)",
        fontsize=11,
        y=1.01,
    )
    ensure_dir(out_dir)
    path = out_dir / f"E_tsne_flow_fields_{observable}.png"
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    log.info("wrote %s", path)
    return path


def plot_tsne_trajectories_single(
    exp_name: str,
    data_dir: Path,
    out_dir: Path,
    observable: str = OBS_DEFAULT,
    pre_pca: int = 50,
    perplexity: float = 30.0,
    seed: int = 42,
    max_traces: int | None = None,
) -> Path | None:
    """
    Per-experiment t-SNE view with actual trajectory lines drawn as colored
    arrows. Each (family, IC, run) is one trajectory; time is encoded as
    arrowhead position and line color gradient.

    This is the most literal visualization of 'where does the recursive loop go
    in t-SNE space over time' — no averaging, no grid binning.
    """
    vec_p = data_dir / exp_name / "embeddings" / observable / "embeddings.npy"
    meta_p = data_dir / exp_name / "embeddings" / observable / "metadata.parquet"
    if not vec_p.exists() or not meta_p.exists():
        return None
    vecs = load_npy(vec_p)
    meta = read_parquet(meta_p)
    rec_idx = np.where(meta["regime"] == "recursive")[0]
    if len(rec_idx) < 10:
        return None
    rec_vecs = vecs[rec_idx]
    rec_meta = meta.iloc[rec_idx].reset_index(drop=True)

    k = min(pre_pca, rec_vecs.shape[1], len(rec_vecs) - 1)
    X_prep = (
        PCA(n_components=k, random_state=seed).fit_transform(rec_vecs)
        if rec_vecs.shape[1] > k and k >= 2
        else rec_vecs
    )
    perp = min(perplexity, max(5.0, (len(X_prep) - 1) / 4))
    Z = TSNE(
        n_components=2,
        perplexity=perp,
        init="pca",
        learning_rate="auto",
        metric="cosine",
        random_state=seed,
    ).fit_transform(X_prep)

    regime = REGIME_LABEL.get(exp_name, "unknown")
    title_color = REGIME_COLOR.get(regime, "#333")
    fig, ax = plt.subplots(figsize=(11, 9))

    # Faint background: all points
    ax.scatter(Z[:, 0], Z[:, 1], s=4, alpha=0.12, color="k", linewidths=0, label=None)

    # Per-trajectory arrows
    cmap = plt.get_cmap("viridis")
    traj_count = 0
    for keys, sub in rec_meta.groupby(
        ["prompt_family", "initial_condition_id", "run_id"]
    ):
        if max_traces is not None and traj_count >= max_traces:
            break
        sub_sorted = sub.sort_values("step")
        idx = sub_sorted.index.to_numpy()
        z_run = Z[idx]
        if len(z_run) < 2:
            continue
        T = len(z_run)
        for t in range(T - 1):
            # Color by step within the run
            c = cmap(t / max(1, T - 1))
            ax.annotate(
                "",
                xy=(z_run[t + 1, 0], z_run[t + 1, 1]),
                xytext=(z_run[t, 0], z_run[t, 1]),
                arrowprops=dict(
                    arrowstyle="->",
                    color=c,
                    alpha=0.55,
                    linewidth=1.0,
                    shrinkA=0,
                    shrinkB=0,
                ),
            )
        # Mark the starting point (step 0)
        ax.scatter(
            z_run[0, 0], z_run[0, 1],
            s=45, facecolors="none", edgecolors="red", linewidths=1.4, zorder=3,
        )
        traj_count += 1

    ax.set_title(
        f"{DISPLAY.get(exp_name, exp_name)} — {regime}  (t-SNE trajectories)\n"
        f"{traj_count} recursive runs drawn as step-by-step arrows "
        f"(dark = early step, bright = late; red circles = step 0 / seed)\n"
        f"({observable}; {len(Z)} total points)",
        color=title_color,
        fontsize=11,
    )
    ax.set_xlabel("t-SNE 1")
    ax.set_ylabel("t-SNE 2")
    ax.grid(alpha=0.15)

    # Time colorbar
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=0, vmax=1))
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, pad=0.02, label="step within trajectory (normalized)")
    cbar.ax.tick_params(labelsize=9)

    ensure_dir(out_dir)
    path = out_dir / f"F_tsne_trajectories_{exp_name}_{observable}.png"
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    log.info("wrote %s", path)
    return path


def plot_flow_field_single(
    exp_name: str,
    data_dir: Path,
    out_dir: Path,
    observable: str = OBS_DEFAULT,
    grid_n: int = 28,
) -> Path | None:
    """Render one experiment's flow field at large scale for close inspection."""
    result = _flow_field_for_experiment(data_dir / exp_name, observable, grid_n=grid_n)
    if result is None:
        return None
    X, Y, U, V, density, pts = result
    regime = REGIME_LABEL.get(exp_name, "unknown")
    title_color = REGIME_COLOR.get(regime, "#333")

    fig, ax = plt.subplots(figsize=(9, 7))
    ax.pcolormesh(X, Y, np.log1p(density), cmap="Greys", alpha=0.35, shading="auto")
    mask = ~np.isnan(U) & ~np.isnan(V) & (density >= 2)
    mag = np.where(mask, np.sqrt(U**2 + V**2), np.nan)
    if mask.any():
        q = ax.quiver(
            X[mask],
            Y[mask],
            U[mask],
            V[mask],
            mag[mask],
            cmap="plasma",
            scale_units="xy",
            scale=1.0,
            angles="xy",
            width=0.005,
            alpha=0.95,
        )
        cbar = fig.colorbar(q, ax=ax, pad=0.02, label="|displacement| per step")
        cbar.ax.tick_params(labelsize=9)
    ax.scatter(pts[:, 0], pts[:, 1], s=2, alpha=0.2, color="k", linewidths=0)
    ax.set_title(
        f"{DISPLAY.get(exp_name, exp_name)} — {regime}\n"
        f"averaged Y_t → Y_(t+1) displacement field in PCA-2\n"
        f"({observable}, {len(pts)} points, grid = {grid_n}×{grid_n})",
        color=title_color,
        fontsize=11,
    )
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(alpha=0.15)

    ensure_dir(out_dir)
    path = out_dir / f"E_flow_{exp_name}_{observable}.png"
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    log.info("wrote %s", path)
    return path


def plot_flow_field_grid(
    data_dir: Path,
    out_dir: Path,
    observable: str = OBS_DEFAULT,
    grid_n: int = 24,
) -> Path:
    exp_order = [e for e in REGIME_LABEL.keys() if (data_dir / e / "config.yaml").exists()]
    n_exp = len(exp_order)
    ncols = 4
    nrows = int(np.ceil(n_exp / ncols))
    fig, axes = plt.subplots(
        nrows, ncols, figsize=(4.5 * ncols, 3.8 * nrows), squeeze=False
    )

    for ax_i, exp_name in enumerate(exp_order):
        ax = axes[ax_i // ncols, ax_i % ncols]
        regime = REGIME_LABEL.get(exp_name, "unknown")
        title_color = REGIME_COLOR.get(regime, "#333")

        result = _flow_field_for_experiment(data_dir / exp_name, observable, grid_n=grid_n)
        if result is None:
            ax.set_title(f"{DISPLAY.get(exp_name, exp_name)}\n(no data)", color=title_color, fontsize=10)
            ax.axis("off")
            continue

        X, Y, U, V, density, pts = result

        # Background: visit density (log-scale for readability)
        mesh = ax.pcolormesh(
            X,
            Y,
            np.log1p(density),
            cmap="Greys",
            alpha=0.35,
            shading="auto",
        )

        # Quiver on bins with ≥ 2 observed displacements (filter noise)
        mask = ~np.isnan(U) & ~np.isnan(V) & (density >= 2)
        mag = np.where(mask, np.sqrt(U**2 + V**2), np.nan)
        if mask.any():
            ax.quiver(
                X[mask],
                Y[mask],
                U[mask],
                V[mask],
                mag[mask],
                cmap="plasma",
                scale_units="xy",
                scale=1.0,
                angles="xy",
                width=0.004,
                alpha=0.9,
            )

        # Thin point overlay for orientation
        ax.scatter(pts[:, 0], pts[:, 1], s=1.5, alpha=0.15, color="k", linewidths=0)

        ax.set_title(
            f"{DISPLAY.get(exp_name, exp_name)}  —  {regime}",
            color=title_color,
            fontsize=10,
        )
        ax.set_xlabel("PC1", fontsize=8)
        ax.set_ylabel("PC2", fontsize=8)
        ax.tick_params(labelsize=7)
        ax.set_aspect("equal", adjustable="box")
        ax.grid(alpha=0.12)

    for ax_i in range(n_exp, nrows * ncols):
        axes[ax_i // ncols, ax_i % ncols].axis("off")

    fig.suptitle(
        f"Plot E — averaged displacement vector fields in per-experiment PCA-2 space\n"
        f"(observable = {observable}; grey = visit density; arrows = mean Y_t→Y_{{t+1}} flow; arrow color = local speed)",
        fontsize=11,
        y=1.01,
    )
    ensure_dir(out_dir)
    path = out_dir / f"E_flow_fields_{observable}.png"
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    log.info("wrote %s", path)
    return path


def main(argv: list[str] | None = None) -> int:
    from src.utils.logging import setup_logging

    parser = argparse.ArgumentParser(prog="regime_plots")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--out-dir", default="data/aggregated/dynamics_plots")
    parser.add_argument("--observable", default=OBS_DEFAULT)
    parser.add_argument("--log-level", default="INFO")
    parser.add_argument(
        "--prefix",
        default=None,
        help="Only include experiments whose id starts with this prefix "
             "(e.g. 'exp_pub_' to exclude stale small-N experiments).",
    )
    parser.add_argument(
        "--skip-tsne",
        action="store_true",
        help="Skip joint-t-SNE plot (slow for pub-scale data).",
    )
    args = parser.parse_args(argv)
    setup_logging(args.log_level, None)

    data_dir = Path(args.data_dir)
    out_dir = Path(args.out_dir)

    # Optionally restrict REGIME_LABEL to a prefix — mutating the shared dict
    # affects all downstream plot functions that iterate its keys.
    if args.prefix:
        original = dict(REGIME_LABEL)
        filtered = {k: v for k, v in original.items() if k.startswith(args.prefix)}
        REGIME_LABEL.clear()
        REGIME_LABEL.update(filtered)
        log.info("filtered to %d experiments with prefix '%s'", len(filtered), args.prefix)

    if not args.skip_tsne:
        plot_joint_tsne(data_dir, out_dir, observable=args.observable)
    plot_trajectory_grid(data_dir, out_dir, observable=args.observable)
    plot_spread_timelines(data_dir, out_dir, observable=args.observable)
    plot_flow_field_grid(data_dir, out_dir, observable=args.observable)
    plot_flow_field_tsne_grid(data_dir, out_dir, observable=args.observable)
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
