"""
Multi-granularity switching analysis.

Extends §5.10.6 cluster-stability finding (HDBSCAN sees O1 as 2
clusters, not 12). Question: does the dose-response switching curve
survive at HDBSCAN's coarser granularity? If switching rate stays
meaningful at the *true* basin count, that's strong evidence the
headline isn't an artefact of choosing K-means k=12.

Approach
--------
For each existing perturbation pilot in `data/exp_perturb_O*_pilot/`:

1. Load the joint PCA-10 cloud (control + 3 perturbed conditions).
2. Re-cluster at three granularities:
     - K-means k=12 (the canonical paper choice)
     - K-means k=4
     - HDBSCAN (auto)
3. For each trajectory (regime, family, IC, run), compute its final-
   step cluster under each granularity.
4. For each non-control trajectory, check whether its final cluster
   differs from its paired control's final cluster — separately for
   each granularity.
5. Report switching rate per (condition × granularity) cell with
   Wilson CI. The headline number is the dose-response slope; we
   look at how it changes when granularity changes.

Output
------
data/<exp>/reports/perturbation/multi_granularity_switching.csv
data/<exp>/reports/perturbation/multi_granularity_switching.png

Usage
-----
    python -m scripts.multi_granularity_switching
    # default scans the four diagnostic perturbation pilots
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
from sklearn.cluster import HDBSCAN, KMeans

REPO = Path(__file__).resolve().parent.parent

DEFAULT_EXPERIMENTS = [
    "exp_perturb_O1_pilot",
    "exp_perturb_O2_pilot",
    "exp_perturb_O3_pilot",
    "exp_perturb_D1_pilot",
]


def _load_joint_cloud(exp_dir: Path) -> pd.DataFrame | None:
    p = exp_dir / "reports" / "perturbation" / "joint_pca10_clusters.csv"
    if not p.exists():
        return None
    return pd.read_csv(p)


def _wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = (z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def _re_cluster(
    df: pd.DataFrame, k_canonical: int = 12, k_coarse: int = 4,
) -> pd.DataFrame:
    """Add cluster columns for kmeans@k_canonical, kmeans@k_coarse,
    and hdbscan-auto, computed on the joint PCA-10 cloud."""
    pc_cols = [f"pc{i}" for i in range(1, 11)]
    X = df[pc_cols].to_numpy()
    df = df.copy()
    print(f"  re-clustering {len(df)} points...")
    df["cluster_kmeans12"] = KMeans(
        n_clusters=k_canonical, random_state=42, n_init=10,
    ).fit_predict(X)
    df["cluster_kmeans4"] = KMeans(
        n_clusters=k_coarse, random_state=42, n_init=10,
    ).fit_predict(X)
    hdb = HDBSCAN(
        min_cluster_size=max(50, len(df) // 100), min_samples=10,
        allow_single_cluster=False,
    )
    df["cluster_hdbscan"] = hdb.fit_predict(X)
    n_hdb = len(set(df["cluster_hdbscan"].values)) - (
        1 if -1 in df["cluster_hdbscan"].values else 0
    )
    print(f"  HDBSCAN found {n_hdb} clusters "
          f"({(df['cluster_hdbscan'] == -1).sum()} noise points)")
    return df


def _final_cluster(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Final-step cluster per (regime, family, ic, run)."""
    final_step = df.groupby(
        ["regime", "prompt_family", "initial_condition_id", "run_id"]
    )["step"].max().reset_index().rename(columns={"step": "final_step"})
    finals = df.merge(
        final_step,
        left_on=["regime", "prompt_family", "initial_condition_id", "run_id", "step"],
        right_on=["regime", "prompt_family", "initial_condition_id", "run_id", "final_step"],
        how="inner",
    )[["regime", "prompt_family", "initial_condition_id", "run_id", col]]
    return finals


def _switching_rates(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """For each non-control regime, compute switching rate vs same
    (family, ic, run_id) control's final-cluster value under granularity `col`."""
    finals = _final_cluster(df, col)
    ctl = finals[finals["regime"] == "control"].rename(
        columns={col: f"ctl_{col}"}
    ).drop(columns=["regime"])
    pert = finals[finals["regime"] != "control"]
    # Try same-run pairing first.
    paired = pert.merge(
        ctl, on=["prompt_family", "initial_condition_id", "run_id"],
        how="left",
    )
    # Where same-run control is missing, fall back to control run_000.
    ctl_run0 = ctl[ctl["run_id"] == "run_000"][
        ["prompt_family", "initial_condition_id", f"ctl_{col}"]
    ].rename(columns={f"ctl_{col}": f"ctl_{col}_run0"})
    paired = paired.merge(
        ctl_run0, on=["prompt_family", "initial_condition_id"], how="left",
    )
    paired[f"ctl_{col}"] = paired[f"ctl_{col}"].fillna(paired[f"ctl_{col}_run0"])
    paired["switched"] = (paired[col] != paired[f"ctl_{col}"]).astype(int)
    return paired.groupby("regime").agg(
        n_total=("switched", "count"),
        n_switched=("switched", "sum"),
    ).reset_index()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--experiments", nargs="+", default=DEFAULT_EXPERIMENTS)
    args = ap.parse_args()

    overall_rows = []
    for exp in args.experiments:
        exp_dir = REPO / "data" / exp
        print(f"\n=== {exp} ===")
        df = _load_joint_cloud(exp_dir)
        if df is None:
            print(f"  skip: no joint_pca10_clusters.csv")
            continue
        if not all(f"pc{i}" in df.columns for i in range(1, 11)):
            print(f"  skip: missing pc1..pc10 columns")
            continue
        df = _re_cluster(df)
        per_granularity = []
        for col in ["cluster_kmeans12", "cluster_kmeans4", "cluster_hdbscan"]:
            res = _switching_rates(df, col)
            res["granularity"] = col
            res["rate"] = res["n_switched"] / res["n_total"]
            res[["wilson_lo", "wilson_hi"]] = res.apply(
                lambda r: pd.Series(_wilson_ci(int(r["n_switched"]), int(r["n_total"]))),
                axis=1,
            )
            per_granularity.append(res)
            print(f"  {col}:")
            for _, r in res.iterrows():
                print(f"    {r['regime']:25s} {r['rate']:.2f} "
                      f"[{r['wilson_lo']:.2f}, {r['wilson_hi']:.2f}] "
                      f"n={int(r['n_total'])}")
        out = pd.concat(per_granularity, ignore_index=True)
        out["experiment"] = exp
        overall_rows.append(out)
        out_dir = exp_dir / "reports" / "perturbation"
        out.to_csv(out_dir / "multi_granularity_switching.csv", index=False)
        print(f"  wrote {out_dir / 'multi_granularity_switching.csv'}")

    if not overall_rows:
        return 0

    summary = pd.concat(overall_rows, ignore_index=True)
    out = REPO / "data" / "aggregated" / "multi_granularity_switching.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(out, index=False)
    print(f"\nwrote {out}")

    # Plot: per experiment, bar groups by granularity.
    n_exp = summary["experiment"].nunique()
    fig, axes = plt.subplots(1, n_exp, figsize=(4 * n_exp, 5),
                             sharey=True, facecolor="white")
    if n_exp == 1:
        axes = [axes]
    granularities = ["cluster_kmeans12", "cluster_kmeans4", "cluster_hdbscan"]
    granularity_labels = {
        "cluster_kmeans12": "KMeans k=12 (canonical)",
        "cluster_kmeans4": "KMeans k=4 (coarse)",
        "cluster_hdbscan": "HDBSCAN (auto)",
    }
    granularity_colors = {
        "cluster_kmeans12": "#1f77b4",
        "cluster_kmeans4": "#ff7f0e",
        "cluster_hdbscan": "#2ca02c",
    }
    for ax, (exp, sub) in zip(axes, summary.groupby("experiment")):
        regimes = sorted(sub["regime"].unique())
        x = np.arange(len(regimes))
        width = 0.27
        for i, g in enumerate(granularities):
            sg = sub[sub["granularity"] == g].set_index("regime")
            rates = [sg.loc[r, "rate"] if r in sg.index else 0 for r in regimes]
            errs_lo = [sg.loc[r, "rate"] - sg.loc[r, "wilson_lo"] if r in sg.index else 0
                       for r in regimes]
            errs_hi = [sg.loc[r, "wilson_hi"] - sg.loc[r, "rate"] if r in sg.index else 0
                       for r in regimes]
            ax.bar(x + (i - 1) * width, rates, width, yerr=[errs_lo, errs_hi],
                   color=granularity_colors[g],
                   label=granularity_labels[g] if ax is axes[0] else None,
                   capsize=3, ecolor="black", linewidth=0.4, edgecolor="black")
        ax.set_xticks(x)
        ax.set_xticklabels(regimes, fontsize=8, rotation=45, ha="right")
        ax.set_ylim(0, 1.05)
        ax.set_title(exp.replace("exp_perturb_", "").replace("_pilot", ""), fontsize=10)
        ax.axhline(0.5, color="#aaa", linestyle="--", linewidth=0.6)
        ax.set_facecolor("white")
    axes[0].set_ylabel("switching rate vs paired control")
    fig.suptitle("Multi-granularity switching: does the dose-response survive\n"
                 "different cluster definitions? (Wilson 95% CIs)",
                 fontsize=12, y=0.99)
    fig.legend(loc="lower center", ncol=3, fontsize=9, bbox_to_anchor=(0.5, -0.02))
    fig.tight_layout(rect=(0, 0.02, 1, 0.96))
    fig_path = REPO / "data" / "aggregated" / "multi_granularity_switching.png"
    fig.savefig(fig_path, dpi=160, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {fig_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
