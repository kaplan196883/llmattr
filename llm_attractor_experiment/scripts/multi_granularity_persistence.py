"""
Multi-granularity dense-persistence analysis (review round-3 #2).

Applies the persistence test (kicked-at-injection AND persisted-to-final)
under three cluster granularities: K-means k=12 (canonical), K-means k=4
(coarse), HDBSCAN (auto). Operates on the dense ED50 rerun's
joint_pca10_clusters.csv plus a freshly computed alternate-granularity
clustering on the same PCA-10 cloud.

If the persistent-escape rate at the highest dose (400 tokens) survives
across cluster granularities, the gpt-5.5 round-3 review point
"persistent escape is now load-bearing but not multi-granularity
validated" is closed.

Output:
  data/aggregated/multi_granularity_persistence.csv
  data/aggregated/multi_granularity_persistence.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import HDBSCAN, KMeans

REPO = Path(__file__).resolve().parent.parent
EXP = "exp_perturb_O1_ed50_dense"


def _build_alt_clusters(df: pd.DataFrame) -> pd.DataFrame:
    """Compute K-means k=4 and HDBSCAN cluster labels on the joint PCA-10
    cloud already in df. Returns df with new columns `cluster_kmeans4`
    and `cluster_hdbscan` alongside the existing `cluster` (= K-means k=12)."""
    pc_cols = [f"pc{i}" for i in range(1, 11)]
    X = df[pc_cols].to_numpy()
    print(f"  re-clustering {len(X)} points...")
    df = df.copy()
    df["cluster_kmeans12"] = df["cluster"]
    df["cluster_kmeans4"] = KMeans(n_clusters=4, random_state=42, n_init=10).fit_predict(X)
    hdb = HDBSCAN(
        min_cluster_size=max(50, len(df) // 100), min_samples=10,
        allow_single_cluster=False,
    )
    df["cluster_hdbscan"] = hdb.fit_predict(X)
    n_hdb = len(set(df["cluster_hdbscan"].values)) - (
        1 if -1 in df["cluster_hdbscan"].values else 0
    )
    n_noise = (df["cluster_hdbscan"] == -1).sum()
    print(f"  HDBSCAN: {n_hdb} clusters, {n_noise} noise points")
    return df


def _persistence_for_granularity(
    df: pd.DataFrame, cluster_col: str, inject_step: int = 15,
) -> pd.DataFrame:
    """Per perturbed trajectory: pre_inj cluster (step 14), post_inj
    (step 15), final (max step). Compute kicked / persisted /
    drifted_back / drifted_elsewhere counts per condition."""
    pivot = df.pivot_table(
        index=["regime", "prompt_family", "initial_condition_id", "run_id"],
        columns="step", values=cluster_col, aggfunc="first",
    )
    pre_col = inject_step - 1
    post_col = inject_step
    final_step = df["step"].max()
    if not all(c in pivot.columns for c in (pre_col, post_col, final_step)):
        return pd.DataFrame()
    rows = []
    for (regime, fam, ic, run), srow in pivot.iterrows():
        if regime == "control":
            continue
        pre, post, end = srow.get(pre_col), srow.get(post_col), srow.get(final_step)
        if pd.isna(pre) or pd.isna(post) or pd.isna(end):
            continue
        rows.append({
            "regime": regime,
            "kicked": int(post != pre),
            "persisted": int(end == post and post != pre),
            "drifted_back": int(end == pre and post != pre),
            "drifted_elsewhere": int(end != pre and end != post and post != pre),
        })
    df_p = pd.DataFrame(rows)
    if df_p.empty:
        return pd.DataFrame()
    summary = df_p.groupby("regime").agg(
        n_total=("regime", "count"),
        kicked=("kicked", "sum"),
        persisted=("persisted", "sum"),
        drifted_back=("drifted_back", "sum"),
        drifted_elsewhere=("drifted_elsewhere", "sum"),
    ).reset_index()
    summary["pct_kicked"] = summary["kicked"] / summary["n_total"]
    summary["pct_persisted"] = summary["persisted"] / summary["n_total"]
    summary["pct_drifted_back"] = summary["drifted_back"] / summary["n_total"]
    summary["pct_drifted_elsewhere"] = summary["drifted_elsewhere"] / summary["n_total"]
    summary["granularity"] = cluster_col
    return summary


def main() -> int:
    p = REPO / "data" / EXP / "reports" / "perturbation" / "joint_pca10_clusters.csv"
    if not p.exists():
        print(f"error: {p} not found")
        return 1
    df = pd.read_csv(p)
    print(f"loaded {len(df)} rows")
    df = _build_alt_clusters(df)

    parts = []
    for col in ["cluster_kmeans12", "cluster_kmeans4", "cluster_hdbscan"]:
        s = _persistence_for_granularity(df, col)
        if s.empty:
            continue
        parts.append(s)
    out = pd.concat(parts, ignore_index=True)
    # Sort by dose (extracted from regime name) for readability.
    out["dose"] = out["regime"].str.extract(r"adversarial_dose(\d+)").astype(float)
    out = out.sort_values(["granularity", "dose"]).reset_index(drop=True)
    out_path = REPO / "data" / "aggregated" / "multi_granularity_persistence.csv"
    out.to_csv(out_path, index=False)
    print(f"\nwrote {out_path}")
    print(out.to_string(index=False))

    # Plot: per granularity, persistent-escape rate vs dose.
    fig, ax = plt.subplots(figsize=(9, 5.5), facecolor="white")
    granularity_label = {
        "cluster_kmeans12": "K-means k=12 (canonical)",
        "cluster_kmeans4": "K-means k=4 (coarse)",
        "cluster_hdbscan": "HDBSCAN (auto)",
    }
    granularity_color = {
        "cluster_kmeans12": "#1f77b4",
        "cluster_kmeans4": "#ff7f0e",
        "cluster_hdbscan": "#2ca02c",
    }
    for col in ["cluster_kmeans12", "cluster_kmeans4", "cluster_hdbscan"]:
        sub = out[out["granularity"] == col].sort_values("dose")
        ax.plot(
            sub["dose"], sub["pct_persisted"],
            "-o", color=granularity_color[col],
            label=f"{granularity_label[col]} — persistent escape",
            markersize=6,
        )
        ax.plot(
            sub["dose"], sub["pct_kicked"],
            "--^", color=granularity_color[col], alpha=0.6,
            label=f"{granularity_label[col]} — kicked at injection",
            markersize=4,
        )
    ax.axhline(0.5, color="#888", linestyle=":", linewidth=0.7,
               label="50% threshold (formal barrier)")
    ax.set_xscale("log")
    ax.set_xlabel("adversarial dose (tokens)")
    ax.set_ylabel("rate")
    ax.set_title("Persistent-escape rate vs dose under three cluster granularities\n"
                 "(O1 dense rerun; persistent = kicked at injection AND in new cluster at terminal step)")
    ax.set_facecolor("white")
    ax.set_ylim(0, 1.0)
    ax.grid(alpha=0.25, linewidth=0.5)
    ax.legend(loc="upper left", fontsize=8, framealpha=0.95)
    fig.tight_layout()
    fig_path = REPO / "data" / "aggregated" / "multi_granularity_persistence.png"
    fig.savefig(fig_path, dpi=160, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(f"\nwrote {fig_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
