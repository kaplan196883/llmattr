from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.utils.io import ensure_dir


def _save(fig: plt.Figure, path: Path) -> Path:
    ensure_dir(path.parent)
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_trajectories_pca2(
    df: pd.DataFrame,
    observable: str,
    out_dir: Path,
    color_by: str = "run_id",
) -> Path:
    fig, ax = plt.subplots(figsize=(7, 6))
    groups = df.groupby(color_by, dropna=False)
    cmap = plt.get_cmap("tab20", max(1, len(groups)))
    for i, (key, sub) in enumerate(groups):
        sub = sub.sort_values("step")
        ax.plot(sub["pc1"], sub["pc2"], "-", lw=0.6, alpha=0.5, color=cmap(i % cmap.N))
        ax.scatter(sub["pc1"], sub["pc2"], s=6, color=cmap(i % cmap.N))
    ax.set_title(f"PCA-2 trajectories ({observable}) colored by {color_by}")
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    ax.grid(alpha=0.2)
    return _save(fig, out_dir / f"pca2_trajectories_{observable}_by_{color_by}.png")


def plot_time_colored(
    df: pd.DataFrame,
    observable: str,
    out_dir: Path,
) -> Path:
    fig, ax = plt.subplots(figsize=(7, 6))
    sc = ax.scatter(df["pc1"], df["pc2"], c=df["step"], s=8, cmap="viridis")
    plt.colorbar(sc, ax=ax, label="step")
    ax.set_title(f"PCA-2 points time-colored ({observable})")
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    ax.grid(alpha=0.2)
    return _save(fig, out_dir / f"pca2_timecolor_{observable}.png")


def plot_cluster_occupancy(
    cluster_counts: pd.DataFrame, observable: str, out_dir: Path
) -> Path:
    fig, ax = plt.subplots(figsize=(6, 4))
    sub = cluster_counts.sort_values("count", ascending=False)
    ax.bar(sub["cluster"].astype(str), sub["count"])
    ax.set_title(f"Cluster occupancy ({observable})")
    ax.set_xlabel("cluster")
    ax.set_ylabel("count")
    return _save(fig, out_dir / f"cluster_occupancy_{observable}.png")


def plot_recurrence_distribution(
    df: pd.DataFrame, observable: str, out_dir: Path
) -> Path:
    fig, ax = plt.subplots(figsize=(6, 4))
    for regime, sub in df.groupby("regime", dropna=False):
        ax.hist(sub["recurrence_rate"].dropna(), bins=20, alpha=0.5, label=str(regime))
    ax.set_title(f"Recurrence-rate distribution ({observable})")
    ax.set_xlabel("recurrence rate")
    ax.set_ylabel("count")
    ax.legend()
    return _save(fig, out_dir / f"recurrence_dist_{observable}.png")


def plot_dwell_distribution(
    df: pd.DataFrame, observable: str, out_dir: Path
) -> Path:
    if df.empty:
        return out_dir / f"dwell_dist_{observable}.png"
    fig, ax = plt.subplots(figsize=(6, 4))
    for regime, sub in df.groupby("regime", dropna=False):
        ax.hist(sub["mean_dwell"].dropna(), bins=20, alpha=0.5, label=str(regime))
    ax.set_title(f"Mean-dwell distribution ({observable})")
    ax.set_xlabel("mean dwell length")
    ax.set_ylabel("count")
    ax.legend()
    return _save(fig, out_dir / f"dwell_dist_{observable}.png")


def plot_tsne(
    df: pd.DataFrame,
    observable: str,
    out_dir: Path,
    color_by: str,
    title_suffix: str = "",
) -> Path:
    """
    df columns expected: tsne1, tsne2, and a column named `color_by`
    (e.g. prompt_family, run_id, regime, cluster, step).
    """
    fig, ax = plt.subplots(figsize=(7, 6))
    if color_by == "step":
        sc = ax.scatter(df["tsne1"], df["tsne2"], c=df["step"], s=6, cmap="viridis")
        plt.colorbar(sc, ax=ax, label="step")
    else:
        values = df[color_by].astype(str).fillna("nan")
        uniq = sorted(values.unique().tolist())
        cmap = plt.get_cmap("tab20", max(1, len(uniq)))
        for i, v in enumerate(uniq):
            sub = df[values == v]
            ax.scatter(
                sub["tsne1"],
                sub["tsne2"],
                s=6,
                alpha=0.75,
                color=cmap(i % cmap.N),
                label=v if len(uniq) <= 20 else None,
            )
        if len(uniq) <= 20:
            ax.legend(fontsize=7, markerscale=1.2, loc="best")
    ax.set_title(f"t-SNE points ({observable}) colored by {color_by}{title_suffix}")
    ax.set_xlabel("t-SNE 1")
    ax.set_ylabel("t-SNE 2")
    ax.grid(alpha=0.15)
    return _save(fig, out_dir / f"tsne_{observable}_by_{color_by}.png")


def plot_tsne_trajectories(
    df: pd.DataFrame,
    observable: str,
    out_dir: Path,
    color_by: str = "prompt_family",
    max_traces: int = 60,
) -> Path:
    """Draw per-run line traces through t-SNE space so you can see flow, not just points."""
    fig, ax = plt.subplots(figsize=(7, 6))
    groups_key = ["regime", "prompt_family", "initial_condition_id", "run_id"]
    traced = 0
    values = df[color_by].astype(str).fillna("nan")
    uniq = sorted(values.unique().tolist())
    cmap = plt.get_cmap("tab20", max(1, len(uniq)))
    color_index = {v: i for i, v in enumerate(uniq)}
    for keys, sub in df.groupby(groups_key, dropna=False):
        sub = sub.sort_values("step")
        v = str(sub.iloc[0][color_by])
        color = cmap(color_index.get(v, 0) % cmap.N)
        ax.plot(sub["tsne1"], sub["tsne2"], "-", lw=0.5, alpha=0.4, color=color)
        ax.scatter(sub["tsne1"], sub["tsne2"], s=5, color=color)
        traced += 1
        if traced >= max_traces:
            break
    ax.set_title(f"t-SNE trajectories ({observable}) colored by {color_by}")
    ax.set_xlabel("t-SNE 1")
    ax.set_ylabel("t-SNE 2")
    ax.grid(alpha=0.15)
    return _save(fig, out_dir / f"tsne_trajectories_{observable}_by_{color_by}.png")


def plot_late_recurrence_distribution(
    df: pd.DataFrame, observable: str, out_dir: Path, space: str = "pca10"
) -> Path:
    fig, ax = plt.subplots(figsize=(6, 4))
    if df is None or df.empty:
        ax.set_title(f"Late recurrence (no data) — {observable}")
        return _save(fig, out_dir / f"late_recurrence_dist_{observable}.png")
    sub_space = df[df["space"] == space] if "space" in df.columns else df
    for regime, sub in sub_space.groupby("regime", dropna=False):
        vals = sub["recurrence_rate"].dropna()
        if len(vals) == 0:
            continue
        ax.hist(vals, bins=20, alpha=0.5, label=str(regime))
    ax.set_title(f"Late-time recurrence ({observable}, {space})")
    ax.set_xlabel("late recurrence rate")
    ax.set_ylabel("count")
    ax.legend()
    return _save(fig, out_dir / f"late_recurrence_dist_{observable}.png")


def plot_basin_entry_histogram(
    df: pd.DataFrame, observable: str, out_dir: Path, space: str = "pca10"
) -> Path:
    fig, ax = plt.subplots(figsize=(6, 4))
    if df is None or df.empty:
        ax.set_title(f"Basin entry (no data) — {observable}")
        return _save(fig, out_dir / f"basin_entry_hist_{observable}.png")
    sub = df[df["space"] == space] if "space" in df.columns else df
    sub = sub[sub["reached"] == True] if "reached" in sub.columns else sub  # noqa: E712
    if sub.empty:
        ax.text(0.5, 0.5, "no runs reached basin", ha="center", va="center")
    else:
        ax.hist(sub["entry_step"].to_numpy(), bins=30, color="#4a90e2")
        ax.axvline(
            float(sub["entry_step"].median()),
            color="crimson",
            linestyle="--",
            label=f"median = {sub['entry_step'].median():.1f}",
        )
        ax.legend()
    ax.set_title(f"Basin-entry step ({observable}, {space}) — {len(sub)} runs reached")
    ax.set_xlabel("entry step")
    ax.set_ylabel("runs")
    return _save(fig, out_dir / f"basin_entry_hist_{observable}.png")


def plot_exit_return_scatter(
    df: pd.DataFrame, observable: str, out_dir: Path, space: str = "pca10"
) -> Path:
    fig, ax = plt.subplots(figsize=(6, 5))
    if df is None or df.empty:
        ax.set_title(f"Exit / return (no data) — {observable}")
        return _save(fig, out_dir / f"exit_return_scatter_{observable}.png")
    sub = df[df["space"] == space] if "space" in df.columns else df
    sub = sub[sub["regime"] == "recursive"] if "regime" in sub.columns else sub
    if sub.empty:
        ax.text(0.5, 0.5, "no recursive exit/return rows", ha="center", va="center")
    else:
        rng = np.random.default_rng(0)
        jitter_x = rng.uniform(-0.1, 0.1, size=len(sub))
        jitter_y = rng.uniform(-0.1, 0.1, size=len(sub))
        ax.scatter(
            sub["n_exits"].to_numpy() + jitter_x,
            sub["n_returns"].to_numpy() + jitter_y,
            s=24,
            alpha=0.7,
        )
        mx = max(1, int(sub["n_exits"].max()) + 1)
        ax.plot([0, mx], [0, mx], "k--", lw=0.8, alpha=0.5, label="y = x (all exits return)")
        ax.legend()
    ax.set_xlabel("n_exits from target cluster")
    ax.set_ylabel("n_returns")
    ax.set_title(f"Exit / return per run ({observable}, {space}, recursive only)")
    ax.grid(alpha=0.2)
    return _save(fig, out_dir / f"exit_return_scatter_{observable}.png")


def plot_recurrence_vs_late(
    recurrence_df: pd.DataFrame,
    late_recurrence_df: pd.DataFrame,
    observable: str,
    out_dir: Path,
    space: str = "pca10",
) -> Path:
    """Grouped bars: mean global vs late-time recurrence per regime."""
    fig, ax = plt.subplots(figsize=(7, 4))

    def _means(df):
        if df is None or df.empty:
            return {}
        sub = df[df["observable"] == observable] if "observable" in df.columns else df
        sub = sub[sub["space"] == space] if "space" in sub.columns else sub
        if sub.empty:
            return {}
        return sub.groupby("regime")["recurrence_rate"].mean().to_dict()

    g_means = _means(recurrence_df)
    l_means = _means(late_recurrence_df)
    regimes = sorted(set(g_means) | set(l_means))
    if not regimes:
        ax.set_title(f"Recurrence vs late (no data) — {observable}")
        return _save(fig, out_dir / f"recurrence_vs_late_{observable}.png")

    x = np.arange(len(regimes))
    w = 0.4
    g_vals = [g_means.get(r, 0.0) for r in regimes]
    l_vals = [l_means.get(r, 0.0) for r in regimes]
    ax.bar(x - w / 2, g_vals, w, label="global recurrence")
    ax.bar(x + w / 2, l_vals, w, label="late-time recurrence")
    ax.set_xticks(x)
    ax.set_xticklabels(regimes)
    ax.set_ylabel("mean recurrence rate")
    ax.set_title(f"Global vs late-time recurrence ({observable}, {space})")
    ax.legend()
    ax.grid(alpha=0.2, axis="y")
    return _save(fig, out_dir / f"recurrence_vs_late_{observable}.png")


def plot_permutation_effects(perm_df: pd.DataFrame, out_dir: Path) -> Path:
    fig, ax = plt.subplots(figsize=(8, max(4, 0.3 * len(perm_df))))
    if perm_df is None or perm_df.empty:
        ax.set_title("Permutation effects (no data)")
        return _save(fig, out_dir / "permutation_effects.png")

    df = perm_df.copy()
    # Normalize dwell effects so they're not crushed next to recurrence deltas.
    # Show each metric family side by side by sorting.
    df = df.sort_values(["metric", "observable", "space"], ascending=[True, True, True]).reset_index(drop=True)
    labels = [f"{r['metric']} | {r['observable']} | {r['space']}" for _, r in df.iterrows()]
    colors = ["#4a90e2" if v >= 0 else "#e24a4a" for v in df["mean_diff"]]
    y = np.arange(len(df))
    ax.barh(y, df["mean_diff"].to_numpy(), color=colors, edgecolor="black", linewidth=0.3)
    for i, (v, p) in enumerate(zip(df["mean_diff"], df["p_value"])):
        stars = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
        ax.text(
            v + (0.02 * np.sign(v) if v != 0 else 0.02),
            i,
            f" p={p:.3f} {stars}",
            va="center",
            fontsize=7,
        )
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=7)
    ax.axvline(0, color="k", lw=0.5)
    ax.set_xlabel("mean(recursive) − mean(time_shuffled)")
    ax.set_title("Permutation-test effects vs time_shuffled null")
    ax.grid(alpha=0.2, axis="x")
    return _save(fig, out_dir / "permutation_effects.png")


def plot_basin_scores(basin_df: pd.DataFrame, observable: str, out_dir: Path) -> Path:
    if basin_df.empty:
        return out_dir / f"basin_scores_{observable}.png"
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(
        np.arange(len(basin_df)),
        basin_df["basin_score"],
        tick_label=basin_df["prompt_family"].astype(str)
        + "/"
        + basin_df["initial_condition_id"].astype(str),
    )
    ax.set_ylim(0, 1)
    ax.set_ylabel("basin score")
    ax.set_title(f"Basin convergence by initial condition ({observable})")
    plt.xticks(rotation=45, ha="right", fontsize=8)
    return _save(fig, out_dir / f"basin_scores_{observable}.png")
