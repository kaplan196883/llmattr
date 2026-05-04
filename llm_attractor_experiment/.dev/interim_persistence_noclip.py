"""Interim no-clip vs clipped persistence comparison on partial data.

Runs multi_observable_persistence on the ongoing exp_perturb_O1_ed50_dense_noclip
data (currently ~54 trajectories per condition) and compares to the existing
exp_perturb_O1_ed50_dense (n=200/condition).

Outputs side-by-side persistence-rate table per observable.
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

OBSERVABLES = ["output", "rolling_k3", "context_tail"]
N_CLUSTERS = 12
INJECT_STEP = 15
PRE_STEP = 14


def _wilson_ci(p: float, n: int) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    z = 1.959963984540054
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def _persistence(exp_name: str, observable: str) -> pd.DataFrame:
    exp_dir = DATA / exp_name
    X = np.load(exp_dir / "embeddings" / observable / "embeddings.npy")
    meta = pd.read_parquet(exp_dir / "embeddings" / observable / "metadata.parquet")

    pca = PCA(n_components=10, random_state=42)
    Xp = pca.fit_transform(X)
    km = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=10)
    clusters = km.fit_predict(Xp)
    df = meta.copy()
    df["cluster"] = clusters

    pivot = df.pivot_table(
        index=["regime", "prompt_family", "initial_condition_id", "run_id"],
        columns="step", values="cluster", aggfunc="first",
    )
    final_step = int(df["step"].max())
    needed = (PRE_STEP, INJECT_STEP, final_step)
    if not all(c in pivot.columns for c in needed):
        return pd.DataFrame()

    rows = []
    for (regime, fam, ic, run), srow in pivot.iterrows():
        if regime == "control":
            continue
        pre, post, end = srow.get(PRE_STEP), srow.get(INJECT_STEP), srow.get(final_step)
        if pd.isna(pre) or pd.isna(post) or pd.isna(end):
            continue
        rows.append({
            "regime": regime,
            "kicked": int(post != pre),
            "persisted": int(end == post and post != pre),
        })
    if not rows:
        return pd.DataFrame()
    df_p = pd.DataFrame(rows)
    summary = df_p.groupby("regime").agg(
        n_total=("regime", "count"),
        kicked=("kicked", "sum"),
        persisted=("persisted", "sum"),
    ).reset_index()

    def dose(s):
        m = re.match(r"adversarial_dose(\d+)$", s)
        return int(m.group(1)) if m else None

    summary["dose"] = summary["regime"].map(dose)
    summary["pct_kicked"] = summary["kicked"] / summary["n_total"]
    summary["pct_persisted"] = summary["persisted"] / summary["n_total"]
    summary["observable"] = observable
    summary["experiment"] = exp_name
    ci = summary.apply(
        lambda r: _wilson_ci(r["pct_persisted"], r["n_total"]), axis=1, result_type="expand"
    )
    summary["persisted_ci_lo"] = ci[0]
    summary["persisted_ci_hi"] = ci[1]
    return summary.sort_values("dose")


def main() -> None:
    print("=" * 85)
    print("Interim comparison: clipped (full N=200) vs no-clip (partial N~54)")
    print("=" * 85)
    for obs in OBSERVABLES:
        print(f"\n--- {obs} ---")
        clipped = _persistence("exp_perturb_O1_ed50_dense", obs)
        noclip  = _persistence("exp_perturb_O1_ed50_dense_noclip", obs)
        print(f"{'dose':>6s}  {'clipped (N=200)':>20s}  {'no-clip (N~54)':>22s}  {'delta':>10s}")
        print("-" * 65)
        for dose in sorted(set(clipped["dose"]).intersection(set(noclip["dose"]))):
            c = clipped[clipped["dose"] == dose].iloc[0]
            n = noclip[noclip["dose"] == dose].iloc[0]
            delta = n["pct_persisted"] - c["pct_persisted"]
            cstr = f"{c['pct_persisted']:.3f}[{c['persisted_ci_lo']:.2f},{c['persisted_ci_hi']:.2f}]"
            nstr = f"{n['pct_persisted']:.3f}[{n['persisted_ci_lo']:.2f},{n['persisted_ci_hi']:.2f}]"
            print(f"{dose:>6d}  {cstr:>20s}  {nstr:>22s}  {delta:+.3f}")


if __name__ == "__main__":
    main()
