"""
Compute preliminary switching rates from the dense-dose ED50 rerun
WHILE IT IS STILL RUNNING. Useful for a sanity check ("is the curve
shaping up the way we predicted?") without waiting for the full run.

Strict caveat: the numbers from this script will change as the run
completes. Do not put these in the paper.

Reads `data/exp_perturb_O1_ed50_dense/raw/steps.jsonl` (committed
trajectories only, per the manifest). For each completed (regime,
family, IC, run) trajectory at maximum step, computes K-means k=12
cluster on a freshly-fit joint PCA-10 of the committed cloud, then
runs the same paired-control switching definition as
`scripts/fit_ed50_hierarchical.py`.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

REPO = Path(__file__).resolve().parent.parent


def main() -> int:
    exp_dir = REPO / "data" / "exp_perturb_O1_ed50_dense"
    if not exp_dir.is_dir():
        print(f"error: {exp_dir} not found")
        return 1

    # Use the canonical observable's embeddings (which the live pipeline
    # writes after each trajectory; we want only the committed parts).
    vec_p = exp_dir / "embeddings" / "context_tail" / "embeddings.npy"
    meta_p = exp_dir / "embeddings" / "context_tail" / "metadata.parquet"
    if not vec_p.exists():
        print(f"  embeddings not yet written; skipping")
        return 0
    vecs = np.load(vec_p)
    meta = pd.read_parquet(meta_p).reset_index(drop=True)
    print(f"loaded {len(vecs)} embeddings, {meta['regime'].nunique()} conditions")

    # Restrict to committed-trajectories: a (regime, family, IC, run) tuple is
    # complete only if it has all 30 step rows. The pipeline writes embeddings
    # incrementally, so partial trajectories can appear here. Drop them.
    counts = meta.groupby(
        ["regime", "prompt_family", "initial_condition_id", "run_id"]
    ).size()
    complete = counts[counts >= 30].index
    mask = (
        meta.set_index(["regime", "prompt_family", "initial_condition_id", "run_id"])
        .index.isin(complete)
    )
    vecs = vecs[mask]
    meta = meta[mask].reset_index(drop=True)
    print(f"after dropping partial trajectories: {len(vecs)} points, "
          f"{len(complete)} complete trajectories")

    # Joint PCA-10 + K-means k=12 on the committed cloud.
    Z = PCA(n_components=10, random_state=42).fit_transform(vecs)
    labels = KMeans(n_clusters=12, random_state=42, n_init=10).fit_predict(Z)
    df = meta.copy()
    df["cluster"] = labels

    # Final-step cluster per trajectory.
    finals = df.groupby(
        ["regime", "prompt_family", "initial_condition_id", "run_id"]
    ).apply(lambda s: s.loc[s["step"].idxmax(), "cluster"]).reset_index(name="final_cluster")

    # Pair perturbed vs same-(family, IC, run) control; fall back to control run_000.
    ctl = finals[finals["regime"] == "control"]
    pert = finals[finals["regime"] != "control"]
    same_run = pert.merge(
        ctl, on=["prompt_family", "initial_condition_id", "run_id"],
        suffixes=("", "_ctrl"),
    )
    matched = set(zip(
        same_run["prompt_family"], same_run["initial_condition_id"],
        same_run["run_id"], same_run["regime"],
    ))
    fallback_rows = pert[~pert.apply(
        lambda r: (r["prompt_family"], r["initial_condition_id"],
                   r["run_id"], r["regime"]) in matched, axis=1
    )]
    ctl_run0 = ctl[ctl["run_id"] == "run_000"][
        ["prompt_family", "initial_condition_id", "final_cluster"]
    ].rename(columns={"final_cluster": "final_cluster_ctrl"}).drop_duplicates(
        ["prompt_family", "initial_condition_id"]
    )
    fallback = fallback_rows.merge(
        ctl_run0, on=["prompt_family", "initial_condition_id"], how="left",
    )
    paired = pd.concat([same_run, fallback], ignore_index=True, sort=False)
    paired["switched"] = (paired["final_cluster"] != paired["final_cluster_ctrl"]).astype(int)
    paired = paired.dropna(subset=["final_cluster_ctrl"])

    # Aggregate by condition.
    summary = paired.groupby("regime").agg(
        n_total=("switched", "count"),
        n_switched=("switched", "sum"),
    ).reset_index()
    summary["rate"] = summary["n_switched"] / summary["n_total"]

    # Wilson 95% CI.
    z = 1.96
    summary["wilson_lo"] = summary.apply(
        lambda r: max(0.0, ((r["rate"] + z*z/(2*r["n_total"]) - z*np.sqrt(
            r["rate"]*(1-r["rate"])/r["n_total"] + z*z/(4*r["n_total"]**2)
        )) / (1 + z*z/r["n_total"]))),
        axis=1,
    )
    summary["wilson_hi"] = summary.apply(
        lambda r: min(1.0, ((r["rate"] + z*z/(2*r["n_total"]) + z*np.sqrt(
            r["rate"]*(1-r["rate"])/r["n_total"] + z*z/(4*r["n_total"]**2)
        )) / (1 + z*z/r["n_total"]))),
        axis=1,
    )
    print("\nPRELIMINARY SWITCHING RATES (will move as run completes):")
    print(summary.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
