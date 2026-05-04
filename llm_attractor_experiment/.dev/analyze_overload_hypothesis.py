"""Test the 'overload' hypothesis at high doses.

If the dip at dose 2000-3000 reflects perturbation heterogeneity:
  - kicked rate stays high (model IS displaced)
  - persisted (= kicked AND end == post-injection cluster) drops
  - drifted_elsewhere (= kicked AND end != pre AND end != post) rises
  - persisted + drifted_elsewhere (= kicked AND not returned to pre)
    stays high

This script computes those four numbers per dose under context_tail.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

EXPERIMENTS = [
    ("exp_perturb_O1_ed50_dense_noclip", "doses 20-400 (n=200)"),
    ("exp_perturb_O1_ed50_higher_noclip", "doses 600-3000 (n=100)"),
]


def _decompose(exp_name: str) -> pd.DataFrame:
    exp_dir = DATA / exp_name
    X = np.load(exp_dir / "embeddings" / "context_tail" / "embeddings.npy")
    meta = pd.read_parquet(exp_dir / "embeddings" / "context_tail" / "metadata.parquet")
    pca = PCA(n_components=10, random_state=42)
    Xp = pca.fit_transform(X)
    km = KMeans(n_clusters=12, random_state=42, n_init=10)
    df = meta.copy()
    df["cluster"] = km.fit_predict(Xp)
    pivot = df.pivot_table(
        index=["regime", "prompt_family", "initial_condition_id", "run_id"],
        columns="step", values="cluster", aggfunc="first",
    )
    final_step = int(df["step"].max())
    rows = []
    for (regime, fam, ic, run), srow in pivot.iterrows():
        if regime == "control":
            continue
        pre = srow.get(14)
        post = srow.get(15)
        end = srow.get(final_step)
        if pd.isna(pre) or pd.isna(post) or pd.isna(end):
            continue
        kicked = post != pre
        if not kicked:
            cat = "not_kicked"
        elif end == post:
            cat = "persisted_at_injection"
        elif end == pre:
            cat = "drifted_back"
        else:
            cat = "drifted_elsewhere"
        rows.append({"regime": regime, "category": cat})
    df_p = pd.DataFrame(rows)
    counts = df_p.groupby(["regime", "category"]).size().unstack(fill_value=0).reset_index()
    counts["n_total"] = counts.iloc[:, 1:].sum(axis=1)
    for col in ["not_kicked", "persisted_at_injection", "drifted_back", "drifted_elsewhere"]:
        if col not in counts:
            counts[col] = 0
    counts["pct_kicked_total"] = (counts["persisted_at_injection"] + counts["drifted_back"] + counts["drifted_elsewhere"]) / counts["n_total"]
    counts["pct_persisted_at_injection"] = counts["persisted_at_injection"] / counts["n_total"]
    counts["pct_drifted_elsewhere"] = counts["drifted_elsewhere"] / counts["n_total"]
    counts["pct_kicked_and_not_returned"] = (counts["persisted_at_injection"] + counts["drifted_elsewhere"]) / counts["n_total"]

    def dose(s):
        m = re.match(r"adversarial_dose(\d+)$", s)
        return int(m.group(1)) if m else None

    counts["dose"] = counts["regime"].map(dose)
    return counts.sort_values("dose")


def main() -> None:
    parts = []
    for exp, label in EXPERIMENTS:
        print(f"computing {exp} ...")
        parts.append(_decompose(exp))
    full = pd.concat(parts, ignore_index=True)
    print()
    print(f"{'dose':>5s} {'kicked':>8s} {'persist@inj':>12s} {'drift_back':>12s} {'drift_else':>12s} {'kicked&!ret':>13s}")
    for _, r in full.iterrows():
        if pd.isna(r["dose"]):
            continue
        print(f"{int(r['dose']):>5d} {r['pct_kicked_total']:>8.3f} {r['pct_persisted_at_injection']:>12.3f} "
              f"{r.get('drifted_back', 0)/r['n_total']:>12.3f} {r['pct_drifted_elsewhere']:>12.3f} "
              f"{r['pct_kicked_and_not_returned']:>13.3f}")


if __name__ == "__main__":
    main()
