"""Multi-observable persistence on O1 higher-dose no-clip extension.

Extends the same protocol as scripts/multi_observable_persistence.py to
the new exp_perturb_O1_ed50_higher_noclip experiment (doses 600-3000).

Key question: does persistence cross 50% at any tested dose under no-clip
protocol?
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
EXP = "exp_perturb_O1_ed50_higher_noclip"
OUT_DIR = DATA / "aggregated" / "multi_observable_persistence_higher"

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


def _persistence(observable: str) -> pd.DataFrame:
    exp_dir = DATA / EXP
    X = np.load(exp_dir / "embeddings" / observable / "embeddings.npy")
    meta = pd.read_parquet(exp_dir / "embeddings" / observable / "metadata.parquet")
    pca = PCA(n_components=10, random_state=42)
    Xp = pca.fit_transform(X)
    print(f"  {observable}: PCA-10 explained variance: {pca.explained_variance_ratio_.sum():.3f}")
    km = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=10)
    df = meta.copy()
    df["cluster"] = km.fit_predict(Xp)
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
    ci = summary.apply(
        lambda r: _wilson_ci(r["pct_persisted"], r["n_total"]), axis=1, result_type="expand"
    )
    summary["persisted_ci_lo"] = ci[0]
    summary["persisted_ci_hi"] = ci[1]
    return summary.sort_values("dose")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("Computing persistence per observable on higher-dose no-clip data...")
    parts = []
    for obs in OBSERVABLES:
        parts.append(_persistence(obs))
    long = pd.concat(parts, ignore_index=True).sort_values(["observable", "dose"])
    csv_path = OUT_DIR / "long.csv"
    long.to_csv(csv_path, index=False)
    print(f"\nwrote {csv_path}")

    print("\n=== Persistence at higher doses, no-clip ===")
    for obs in OBSERVABLES:
        sub = long[long["observable"] == obs]
        print(f"\n{obs}:")
        print(f"  {'dose':>6s}  {'kicked':>10s}  {'persisted':>15s}  {'95% Wilson CI':>20s}")
        for _, r in sub.iterrows():
            print(f"  {int(r['dose']):>6d}  {r['pct_kicked']:>10.3f}  "
                  f"{r['pct_persisted']:>15.3f}  "
                  f"[{r['persisted_ci_lo']:.3f}, {r['persisted_ci_hi']:.3f}]")


if __name__ == "__main__":
    main()
