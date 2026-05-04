"""Compare destination-coherent persistence under heterogeneous (concatenated
multi-source) vs homogeneous (single-source repeated) perturbations at high doses.

Tests the hypothesis that the §5.1.3 destination-coherent dip at doses
1500/2000/3000 is caused by perturbation heterogeneity. If the hypothesis is
correct, homogeneous perturbations should produce *higher* destination-coherent
rates than heterogeneous at matched dose (less scatter, more commitment to a
single new basin).
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


def _wilson(p, n, z=1.959963984540054):
    if n == 0:
        return (float("nan"), float("nan"))
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def _persistence(exp_name, observable="context_tail"):
    exp_dir = DATA / exp_name
    X = np.load(exp_dir / "embeddings" / observable / "embeddings.npy")
    meta = pd.read_parquet(exp_dir / "embeddings" / observable / "metadata.parquet")
    pca = PCA(n_components=10, random_state=42)
    Xp = pca.fit_transform(X)
    km = KMeans(n_clusters=12, random_state=42, n_init=10)
    df = meta.copy()
    df["cluster"] = km.fit_predict(Xp)
    pivot = df.pivot_table(
        index=["regime", "prompt_family", "initial_condition_id", "run_id"],
        columns="step", values="cluster", aggfunc="first",
    )
    final = int(df["step"].max())
    rows = []
    for (regime, fam, ic, run), srow in pivot.iterrows():
        if regime == "control":
            continue
        pre, post, end = srow.get(14), srow.get(15), srow.get(final)
        if pd.isna(pre) or pd.isna(post) or pd.isna(end):
            continue
        rows.append({
            "regime": regime,
            "kicked": int(post != pre),
            "destination_coherent": int(end == post and post != pre),
            "source_basin_escape": int(end != pre and post != pre),
        })
    df_p = pd.DataFrame(rows)
    summary = df_p.groupby("regime").agg(
        n_total=("regime", "count"),
        n_kicked=("kicked", "sum"),
        n_destcoh=("destination_coherent", "sum"),
        n_srcesc=("source_basin_escape", "sum"),
    ).reset_index()

    def dose(s):
        for prefix in ("adversarial_homogeneous_dose", "adversarial_dose"):
            if s.startswith(prefix):
                try:
                    return int(s[len(prefix):])
                except ValueError:
                    return None
        return None

    summary["dose"] = summary["regime"].map(dose)
    summary["pct_kicked"] = summary["n_kicked"] / summary["n_total"]
    summary["pct_destcoh"] = summary["n_destcoh"] / summary["n_total"]
    summary["pct_srcesc"] = summary["n_srcesc"] / summary["n_total"]
    ci_dc = summary.apply(
        lambda r: _wilson(r["pct_destcoh"], r["n_total"]), axis=1, result_type="expand"
    )
    summary["destcoh_lo"] = ci_dc[0]
    summary["destcoh_hi"] = ci_dc[1]
    return summary.dropna(subset=["dose"]).sort_values("dose")


def main():
    print("Heterogeneous (concatenated multi-source) — exp_perturb_O1_ed50_higher_noclip:")
    het = _persistence("exp_perturb_O1_ed50_higher_noclip")
    for _, r in het.iterrows():
        print(f"  dose {int(r['dose']):>5d}  kicked {r['pct_kicked']:.3f}  "
              f"destcoh {r['pct_destcoh']:.3f} [{r['destcoh_lo']:.2f}, {r['destcoh_hi']:.2f}]  "
              f"srcesc {r['pct_srcesc']:.3f}")

    print("\nHomogeneous (single source repeated) — exp_perturb_O1_homogeneous_control:")
    hom = _persistence("exp_perturb_O1_homogeneous_control")
    for _, r in hom.iterrows():
        print(f"  dose {int(r['dose']):>5d}  kicked {r['pct_kicked']:.3f}  "
              f"destcoh {r['pct_destcoh']:.3f} [{r['destcoh_lo']:.2f}, {r['destcoh_hi']:.2f}]  "
              f"srcesc {r['pct_srcesc']:.3f}")

    print("\nDirect comparison at matched doses (heterogeneous vs homogeneous, destination-coherent):")
    print(f"{'dose':>5s}  {'het destcoh':>15s}  {'hom destcoh':>15s}  {'delta (hom-het)':>15s}")
    for d in (1500, 2000, 3000):
        h_row = het[het["dose"] == d]
        m_row = hom[hom["dose"] == d]
        if h_row.empty or m_row.empty:
            continue
        h = h_row.iloc[0]["pct_destcoh"]
        m = m_row.iloc[0]["pct_destcoh"]
        print(f"{d:>5d}  {h:>15.3f}  {m:>15.3f}  {m-h:>+15.3f}")

    out_dir = DATA / "aggregated" / "homogeneous_control"
    out_dir.mkdir(parents=True, exist_ok=True)
    pd.concat([het.assign(perturbation_type="heterogeneous"),
               hom.assign(perturbation_type="homogeneous")]).to_csv(
        out_dir / "comparison.csv", index=False
    )
    print(f"\nwrote {out_dir/'comparison.csv'}")


if __name__ == "__main__":
    main()
