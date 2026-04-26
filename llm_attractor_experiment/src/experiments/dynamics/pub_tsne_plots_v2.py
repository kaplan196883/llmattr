"""
Clarity-upgrade t-SNE plots for publication-scale experiments.

Tier 1 — dark-theme joint t-SNE, recursive-only, bigger markers, saturated palette.
Tier 2 — per-family N-panel grid with family-local t-SNE fits (each re-computes
         t-SNE on only that family's recursive points so basins inside a family
         are visible).
Tier 3 — step-parity joint t-SNE (odd vs even step overlay). Diagnostic for
         period-2 orbits: two well-separated clouds → 2-cycle.

Reads cached t-SNE from data/<exp>/metrics/tsne_<observable>.csv for tiers 1 and
3, and cached embeddings from data/<exp>/embeddings/<observable>/embeddings.npy
for tier 2.
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
from src.utils.io import ensure_dir, load_npy, read_parquet
from src.utils.logging import get_logger, setup_logging

log = get_logger(__name__)

# Saturated 15-color palette (tab10 repeated once + distinct accent).
FAMILY_PALETTE = [
    "#e41a1c", "#377eb8", "#4daf4a", "#984ea3", "#ff7f00",
    "#ffff33", "#a65628", "#f781bf", "#999999", "#66c2a5",
    "#fc8d62", "#8da0cb", "#e78ac3", "#a6d854", "#ffd92f",
]


def _dark_rc():
    return {
        "figure.facecolor": "#0a0a0a",
        "axes.facecolor": "#0a0a0a",
        "axes.edgecolor": "#888",
        "axes.labelcolor": "#ddd",
        "xtick.color": "#aaa",
        "ytick.color": "#aaa",
        "text.color": "#eee",
        "axes.titlecolor": "#eee",
        "savefig.facecolor": "#0a0a0a",
    }


def plot_v2_by_family(df: pd.DataFrame, out_dir: Path, observable: str, exp_id: str) -> Path:
    rec = df[df["regime"] == "recursive"]
    families = sorted(rec["prompt_family"].unique())
    fam_color = {f: FAMILY_PALETTE[i % len(FAMILY_PALETTE)] for i, f in enumerate(families)}

    with plt.rc_context(_dark_rc()):
        fig, ax = plt.subplots(figsize=(14, 10))
        for fam in families:
            sub = rec[rec["prompt_family"] == fam]
            ax.scatter(
                sub["tsne1"], sub["tsne2"],
                s=5, alpha=0.7, color=fam_color[fam],
                label=f"{fam}  (n={len(sub):,})", linewidths=0,
            )
        ax.set_title(
            f"{exp_id} — joint t-SNE of RECURSIVE {observable} "
            f"embeddings, {len(families)} families   [dark-theme v2]",
            fontsize=12, pad=12,
        )
        ax.set_xlabel("t-SNE 1")
        ax.set_ylabel("t-SNE 2")
        leg = ax.legend(
            loc="upper left", bbox_to_anchor=(1.01, 1.0),
            fontsize=9, markerscale=2.5, frameon=False, labelcolor="#eee",
        )
        ax.grid(alpha=0.12, color="#333")
    p = out_dir / f"A_v2_joint_by_family_{observable}.png"
    fig.savefig(p, dpi=140, bbox_inches="tight")
    plt.close(fig)
    log.info("wrote %s", p)
    return p


def plot_v2_by_step(df: pd.DataFrame, out_dir: Path, observable: str, exp_id: str) -> Path:
    rec = df[df["regime"] == "recursive"]
    with plt.rc_context(_dark_rc()):
        fig, ax = plt.subplots(figsize=(13, 10))
        sc = ax.scatter(
            rec["tsne1"], rec["tsne2"],
            c=rec["step"], s=4, alpha=0.75, cmap="plasma", linewidths=0,
        )
        cbar = fig.colorbar(sc, ax=ax, pad=0.02, label="step")
        cbar.ax.tick_params(labelsize=9, colors="#ccc")
        cbar.ax.yaxis.label.set_color("#ddd")
        ax.set_title(
            f"{exp_id} — joint t-SNE, time-colored ({observable})\n"
            f"dark purple → bright yellow: within-basin time progression  [v2 dark]",
            fontsize=12, pad=12,
        )
        ax.set_xlabel("t-SNE 1")
        ax.set_ylabel("t-SNE 2")
        ax.grid(alpha=0.12, color="#333")
    p = out_dir / f"A_v2_joint_by_step_{observable}.png"
    fig.savefig(p, dpi=140, bbox_inches="tight")
    plt.close(fig)
    log.info("wrote %s", p)
    return p


def plot_v2_by_regime(df: pd.DataFrame, out_dir: Path, observable: str, exp_id: str) -> Path | None:
    rec = df[df["regime"] == "recursive"]
    nf = df[df["regime"] == "no_feedback"]
    shuf = df[df["regime"] == "time_shuffled"]
    if len(nf) == 0 and len(shuf) == 0:
        log.info("skipping by_regime plot: only recursive regime present for %s", observable)
        return None

    with plt.rc_context(_dark_rc()):
        fig, ax = plt.subplots(figsize=(13, 10))
        ax.scatter(
            rec["tsne1"], rec["tsne2"], s=4, alpha=0.45, color="#ff8a4a",
            label=f"recursive  (n={len(rec):,})", linewidths=0,
        )
        if len(nf) > 0:
            ax.scatter(
                nf["tsne1"], nf["tsne2"], s=4, alpha=0.85, color="#4aa8ff",
                label=f"no_feedback  (n={len(nf):,})", linewidths=0,
            )
        if len(shuf) > 0:
            ax.scatter(
                shuf["tsne1"], shuf["tsne2"], s=4, alpha=0.85, color="#9aff4a",
                label=f"time_shuffled  (n={len(shuf):,})", linewidths=0,
            )
        subtitle = (
            "baseline forms tight point-like clumps; recursive forms diffuse filaments"
            if len(nf) > 0
            else "recursive vs time_shuffled baseline"
        )
        ax.set_title(
            f"{exp_id} — joint t-SNE, recursive vs baseline ({observable})\n"
            f"{subtitle}  [v2]",
            fontsize=12, pad=12,
        )
        ax.set_xlabel("t-SNE 1")
        ax.set_ylabel("t-SNE 2")
        ax.legend(loc="best", fontsize=11, markerscale=3.0, frameon=False, labelcolor="#eee")
        ax.grid(alpha=0.12, color="#333")
    p = out_dir / f"A_v2_joint_by_regime_{observable}.png"
    fig.savefig(p, dpi=140, bbox_inches="tight")
    plt.close(fig)
    log.info("wrote %s", p)
    return p


def plot_v2_by_step_parity(df: pd.DataFrame, out_dir: Path, observable: str, exp_id: str) -> Path:
    """
    Step-parity overlay — the 2-cycle diagnostic.

    Colors even-step points one color, odd-step points another. If the recursive
    loop locks into a period-2 orbit, the two clouds will occupy disjoint regions
    of t-SNE space. A point-attractor or multi-basin regime shows the two clouds
    fully overlapping.
    """
    rec = df[df["regime"] == "recursive"].copy()
    rec["parity"] = (rec["step"].astype(int) % 2).astype(int)
    even = rec[rec["parity"] == 0]
    odd = rec[rec["parity"] == 1]

    with plt.rc_context(_dark_rc()):
        fig, ax = plt.subplots(figsize=(13, 10))
        ax.scatter(
            even["tsne1"], even["tsne2"], s=5, alpha=0.55, color="#ff5a7a",
            label=f"even step  (n={len(even):,})", linewidths=0,
        )
        ax.scatter(
            odd["tsne1"], odd["tsne2"], s=5, alpha=0.55, color="#5acaff",
            label=f"odd step   (n={len(odd):,})", linewidths=0,
        )
        ax.set_title(
            f"{exp_id} — joint t-SNE, step-parity overlay ({observable})\n"
            f"pink = even step (0,2,4,...); blue = odd step (1,3,5,...); "
            f"separated clouds = period-2 orbit  [v2 parity]",
            fontsize=12, pad=12,
        )
        ax.set_xlabel("t-SNE 1")
        ax.set_ylabel("t-SNE 2")
        ax.legend(loc="best", fontsize=11, markerscale=2.8, frameon=False, labelcolor="#eee")
        ax.grid(alpha=0.12, color="#333")
    p = out_dir / f"A_v2_joint_by_parity_{observable}.png"
    fig.savefig(p, dpi=140, bbox_inches="tight")
    plt.close(fig)
    log.info("wrote %s", p)
    return p


# ---------- Tier 2: per-family panels with family-local t-SNE fits ----------


def plot_v2_per_family_grid(
    cfg, observable: str, out_dir: Path, perplexity: float = 30.0, seed: int = 42
) -> Path:
    vec_p = cfg.embeddings_dir / observable / "embeddings.npy"
    meta_p = cfg.embeddings_dir / observable / "metadata.parquet"
    vecs = load_npy(vec_p)
    meta = read_parquet(meta_p)
    rec_idx = np.where(meta["regime"] == "recursive")[0]
    rec_vecs = vecs[rec_idx]
    rec_meta = meta.iloc[rec_idx].reset_index(drop=True)

    families = sorted(rec_meta["prompt_family"].unique())
    n_fam = len(families)
    ncols = 3
    nrows = int(np.ceil(n_fam / ncols))

    with plt.rc_context(_dark_rc()):
        fig, axes = plt.subplots(
            nrows, ncols, figsize=(5.2 * ncols, 4.3 * nrows), squeeze=False
        )
        for ax_i, fam in enumerate(families):
            ax = axes[ax_i // ncols, ax_i % ncols]
            mask = (rec_meta["prompt_family"] == fam).values
            log.info("t-SNE fit for family '%s' (%d pts)", fam, mask.sum())
            X = rec_vecs[mask]
            meta_fam = rec_meta[mask].reset_index(drop=True)

            # PCA-50 → t-SNE-2
            k = min(50, X.shape[1], len(X) - 1)
            if X.shape[1] > k and k >= 2:
                X_prep = PCA(n_components=k, random_state=seed).fit_transform(X)
            else:
                X_prep = X
            perp = min(perplexity, max(5.0, (len(X_prep) - 1) / 4))
            Z = TSNE(
                n_components=2,
                perplexity=perp,
                init="pca",
                learning_rate="auto",
                metric="cosine",
                random_state=seed,
            ).fit_transform(X_prep)

            # Color by IC (30 colors). Use hsv colormap.
            ics = sorted(meta_fam["initial_condition_id"].unique())
            ic_cmap = plt.get_cmap("hsv", max(1, len(ics)))
            for i_ic, ic in enumerate(ics):
                ic_mask = (meta_fam["initial_condition_id"] == ic).values
                ax.scatter(
                    Z[ic_mask, 0], Z[ic_mask, 1],
                    s=4, alpha=0.7, color=ic_cmap(i_ic / max(1, len(ics) - 1)),
                    linewidths=0,
                )
            ax.set_title(
                f"{fam}  —  {len(ics)} ICs × {len(meta_fam['run_id'].unique())} runs "
                f"× {len(meta_fam) // (len(ics) * 3)} steps",
                fontsize=10, pad=6,
            )
            ax.set_xlabel("t-SNE 1", fontsize=8)
            ax.set_ylabel("t-SNE 2", fontsize=8)
            ax.tick_params(labelsize=7)
            ax.grid(alpha=0.12, color="#333")

        for ax_i in range(n_fam, nrows * ncols):
            axes[ax_i // ncols, ax_i % ncols].axis("off")

        pts_per_fam = len(rec_vecs) // max(1, n_fam)
        n_ics_any = len(sorted(rec_meta["initial_condition_id"].unique()))
        n_runs_any = len(sorted(rec_meta["run_id"].unique()))
        n_steps_any = pts_per_fam // max(1, n_ics_any * n_runs_any)
        fig.suptitle(
            f"{cfg.experiment_id} — per-family t-SNE (local fit, each ~{pts_per_fam:,} points, "
            f"{n_ics_any} ICs colored by hue)\n"
            f"each small cluster is one (IC, run)'s {n_steps_any}-step trajectory  [{observable}]",
            fontsize=13, y=1.005,
        )

    p = out_dir / f"B_v2_per_family_grid_{observable}.png"
    fig.savefig(p, dpi=140, bbox_inches="tight")
    plt.close(fig)
    log.info("wrote %s", p)
    return p


def plot_v2_per_family_parity_grid(
    cfg, observable: str, out_dir: Path, perplexity: float = 30.0, seed: int = 42
) -> Path:
    """
    Family-local t-SNE fits colored by step parity (even vs odd).

    Each panel shows one family's recursive points after a fresh t-SNE fit,
    colored by step % 2. Within each family's local geometry, a period-2 orbit
    shows up as pink and blue forming two distinct sub-structures.
    """
    vec_p = cfg.embeddings_dir / observable / "embeddings.npy"
    meta_p = cfg.embeddings_dir / observable / "metadata.parquet"
    vecs = load_npy(vec_p)
    meta = read_parquet(meta_p)
    rec_idx = np.where(meta["regime"] == "recursive")[0]
    rec_vecs = vecs[rec_idx]
    rec_meta = meta.iloc[rec_idx].reset_index(drop=True)

    families = sorted(rec_meta["prompt_family"].unique())
    n_fam = len(families)
    ncols = 3 if n_fam > 6 else 3
    nrows = int(np.ceil(n_fam / ncols))

    with plt.rc_context(_dark_rc()):
        fig, axes = plt.subplots(
            nrows, ncols, figsize=(5.2 * ncols, 4.3 * nrows), squeeze=False
        )
        for ax_i, fam in enumerate(families):
            ax = axes[ax_i // ncols, ax_i % ncols]
            mask = (rec_meta["prompt_family"] == fam).values
            log.info("parity t-SNE fit for family '%s' (%d pts)", fam, mask.sum())
            X = rec_vecs[mask]
            meta_fam = rec_meta[mask].reset_index(drop=True)

            k = min(50, X.shape[1], len(X) - 1)
            if X.shape[1] > k and k >= 2:
                X_prep = PCA(n_components=k, random_state=seed).fit_transform(X)
            else:
                X_prep = X
            perp = min(perplexity, max(5.0, (len(X_prep) - 1) / 4))
            Z = TSNE(
                n_components=2,
                perplexity=perp,
                init="pca",
                learning_rate="auto",
                metric="cosine",
                random_state=seed,
            ).fit_transform(X_prep)

            parity = (meta_fam["step"].astype(int).values % 2)
            ax.scatter(
                Z[parity == 0, 0], Z[parity == 0, 1],
                s=5, alpha=0.55, color="#ff5a7a", label="even", linewidths=0,
            )
            ax.scatter(
                Z[parity == 1, 0], Z[parity == 1, 1],
                s=5, alpha=0.55, color="#5acaff", label="odd", linewidths=0,
            )
            ax.set_title(fam, fontsize=10, pad=6)
            ax.set_xlabel("t-SNE 1", fontsize=8)
            ax.set_ylabel("t-SNE 2", fontsize=8)
            ax.tick_params(labelsize=7)
            ax.grid(alpha=0.12, color="#333")

        for ax_i in range(n_fam, nrows * ncols):
            axes[ax_i // ncols, ax_i % ncols].axis("off")

        # One legend for the whole figure
        handles, labels = axes[0, 0].get_legend_handles_labels()
        fig.legend(
            handles, labels, loc="upper right", bbox_to_anchor=(0.99, 0.99),
            fontsize=11, markerscale=2.5, frameon=False, labelcolor="#eee",
        )
        fig.suptitle(
            f"{cfg.experiment_id} — per-family t-SNE, step-parity overlay ({observable})\n"
            f"pink = even step, blue = odd step; separated clouds within a family = period-2 orbit",
            fontsize=13, y=1.005,
        )

    p = out_dir / f"B_v2_per_family_parity_{observable}.png"
    fig.savefig(p, dpi=140, bbox_inches="tight")
    plt.close(fig)
    log.info("wrote %s", p)
    return p


def plot_v2_single_ic_trajectories(
    cfg, observable: str, out_dir: Path, n_ics: int = 6, seed: int = 42
) -> Path:
    """
    Single-IC trajectory demo — the unambiguous 2-cycle / point-attractor visual.

    Picks `n_ics` ICs spanning families, projects each IC's recursive points
    (3 runs × T steps) to 2D via IC-local PCA, draws arrows between consecutive
    steps within each run, colors markers by step parity.

    For a 2-cycle (O2): arrows flip back and forth between two tight clusters.
    For a point attractor (O1/D1): arrows drift inward to a single blob.
    """
    vec_p = cfg.embeddings_dir / observable / "embeddings.npy"
    meta_p = cfg.embeddings_dir / observable / "metadata.parquet"
    vecs = load_npy(vec_p)
    meta = read_parquet(meta_p)
    rec_idx = np.where(meta["regime"] == "recursive")[0]
    rec_vecs = vecs[rec_idx]
    rec_meta = meta.iloc[rec_idx].reset_index(drop=True)

    rng = np.random.default_rng(seed)
    families = sorted(rec_meta["prompt_family"].unique())
    picks: list[tuple[str, str]] = []
    for fam in families:
        ics = sorted(rec_meta.loc[rec_meta["prompt_family"] == fam, "initial_condition_id"].unique())
        if ics:
            picks.append((fam, ics[int(rng.integers(0, len(ics)))]))
        if len(picks) >= n_ics:
            break

    ncols = 3
    nrows = int(np.ceil(len(picks) / ncols))

    with plt.rc_context(_dark_rc()):
        fig, axes = plt.subplots(
            nrows, ncols, figsize=(5.2 * ncols, 4.3 * nrows), squeeze=False
        )
        for i, (fam, ic) in enumerate(picks):
            ax = axes[i // ncols, i % ncols]
            mask = (
                (rec_meta["prompt_family"] == fam)
                & (rec_meta["initial_condition_id"] == ic)
            ).values
            X = rec_vecs[mask]
            meta_ic = rec_meta[mask].reset_index(drop=True)

            k = min(2, X.shape[1], len(X) - 1)
            if k < 2:
                ax.axis("off")
                continue
            Z = PCA(n_components=2, random_state=seed).fit_transform(X)

            runs = sorted(meta_ic["run_id"].unique())
            run_colors = ["#ff5a7a", "#5acaff", "#a6d854"]
            for r_i, run in enumerate(runs):
                rm = (meta_ic["run_id"] == run).values
                order = np.argsort(meta_ic.loc[rm, "step"].values)
                Zr = Z[rm][order]
                steps_r = meta_ic.loc[rm, "step"].values[order]
                # arrows between consecutive steps
                for a, b in zip(Zr[:-1], Zr[1:]):
                    ax.annotate(
                        "",
                        xy=(b[0], b[1]), xytext=(a[0], a[1]),
                        arrowprops=dict(
                            arrowstyle="-|>",
                            color=run_colors[r_i % len(run_colors)],
                            alpha=0.45, lw=0.6,
                            shrinkA=0, shrinkB=0,
                        ),
                    )
                # markers colored by step parity
                parity = (steps_r % 2).astype(int)
                ax.scatter(
                    Zr[parity == 0, 0], Zr[parity == 0, 1],
                    s=22, facecolor="#ff5a7a", edgecolor="#0a0a0a",
                    linewidths=0.4, zorder=3,
                )
                ax.scatter(
                    Zr[parity == 1, 0], Zr[parity == 1, 1],
                    s=22, facecolor="#5acaff", edgecolor="#0a0a0a",
                    linewidths=0.4, zorder=3,
                )
            ax.set_title(f"{fam} / {ic}", fontsize=9, pad=5)
            ax.set_xlabel("PC 1", fontsize=8)
            ax.set_ylabel("PC 2", fontsize=8)
            ax.tick_params(labelsize=7)
            ax.grid(alpha=0.12, color="#333")

        for i in range(len(picks), nrows * ncols):
            axes[i // ncols, i % ncols].axis("off")

        fig.suptitle(
            f"{cfg.experiment_id} — per-IC recursive trajectories, IC-local PCA ({observable})\n"
            f"arrows = step t → t+1 (3 runs per IC, different arrow colors); "
            f"pink = even step, blue = odd step",
            fontsize=12, y=1.002,
        )

    p = out_dir / f"C_v2_single_ic_trajectories_{observable}.png"
    fig.savefig(p, dpi=140, bbox_inches="tight")
    plt.close(fig)
    log.info("wrote %s", p)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pub_tsne_plots_v2")
    parser.add_argument("--config", required=True)
    parser.add_argument("--observable", default="rolling_k3")
    parser.add_argument("--tier", choices=["1", "2", "3", "4", "5", "all", "both"], default="all")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)
    setup_logging(args.log_level, None)
    cfg = load_config(args.config)

    out_dir = cfg.reports_dir / "plots"
    ensure_dir(out_dir)

    tiers = {
        "1": {"1"}, "2": {"2"}, "3": {"3"}, "4": {"4"}, "5": {"5"},
        "both": {"1", "2"}, "all": {"1", "2", "3", "4", "5"},
    }[args.tier]

    if {"1", "3"} & tiers:
        tsne_csv = cfg.metrics_dir / f"tsne_{args.observable}.csv"
        df = pd.read_csv(tsne_csv)
        log.info("loaded %d tsne rows from %s", len(df), tsne_csv.name)

        if "1" in tiers:
            plot_v2_by_family(df, out_dir, args.observable, cfg.experiment_id)
            plot_v2_by_step(df, out_dir, args.observable, cfg.experiment_id)
            plot_v2_by_regime(df, out_dir, args.observable, cfg.experiment_id)
        if "3" in tiers:
            log.info("tier 3: step-parity overlay (2-cycle diagnostic, joint)")
            plot_v2_by_step_parity(df, out_dir, args.observable, cfg.experiment_id)

    if "2" in tiers:
        log.info("tier 2: per-family grid with family-local t-SNE")
        plot_v2_per_family_grid(cfg, args.observable, out_dir)

    if "4" in tiers:
        log.info("tier 4: per-family PARITY grid (per-family 2-cycle diagnostic)")
        plot_v2_per_family_parity_grid(cfg, args.observable, out_dir)

    if "5" in tiers:
        log.info("tier 5: single-IC trajectory demo (per-IC local PCA + arrows)")
        plot_v2_single_ic_trajectories(cfg, args.observable, out_dir)

    return 0


if __name__ == "__main__":
    sys.exit(main())
