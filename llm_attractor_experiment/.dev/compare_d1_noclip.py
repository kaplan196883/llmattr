"""Compare D1 raw switching: clipped vs no-clip.

D1 saturation finding (Fig 1, §5.4) was: D1 neutral switching is high
already at dose 5 and stays high across the sweep (~70-80%). Tested
clipped (max_context=12000) and now with max_context=200000.

Reuses the multi_observable_d1_raw pipeline: agent-role-filtered,
joint PCA-10 + K-means k=12 per observable, terminal-cluster switching
vs control.
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

OBSERVABLES = ["output", "last_agent_turn", "rolling_agent_k3", "context_tail"]
N_CLUSTERS = 12


def _wilson_ci(p: float, n: int) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    z = 1.959963984540054
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def _switching(exp_name: str, observable: str) -> pd.DataFrame:
    exp_dir = DATA / exp_name
    X = np.load(exp_dir / "embeddings" / observable / "embeddings.npy")
    meta = pd.read_parquet(exp_dir / "embeddings" / observable / "metadata.parquet")
    if "role" in meta.columns:
        keep = meta["role"] == "agent"
        X = X[keep.to_numpy()]
        meta = meta.loc[keep].reset_index(drop=True)
    pca = PCA(n_components=10, random_state=42)
    Xp = pca.fit_transform(X)
    km = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=10)
    df = meta.copy()
    df["cluster"] = km.fit_predict(Xp)
    final_step = int(df["step"].max())
    final_rows = df[df["step"] == final_step].copy()
    rows = []
    keys = ["prompt_family", "initial_condition_id", "run_id"]
    for (fam, ic, rid), sub in final_rows.groupby(keys):
        ctrl = sub[sub["regime"] == "control"]
        if ctrl.empty:
            continue
        cc = int(ctrl.iloc[0]["cluster"])
        for _, prow in sub.iterrows():
            if prow["regime"] == "control":
                continue
            rows.append({
                "regime": prow["regime"],
                "switched": int(int(prow["cluster"]) != cc),
            })
    df_p = pd.DataFrame(rows)
    summary = df_p.groupby("regime").agg(
        n_total=("regime", "count"),
        n_switched=("switched", "sum"),
    ).reset_index()
    summary["switch_rate"] = summary["n_switched"] / summary["n_total"]

    def dose(s):
        m = re.match(r"neutral_dose(\d+)$", s)
        return int(m.group(1)) if m else None

    summary["dose"] = summary["regime"].map(dose)
    ci = summary.apply(
        lambda r: _wilson_ci(r["switch_rate"], r["n_total"]), axis=1, result_type="expand"
    )
    summary["ci_lo"] = ci[0]
    summary["ci_hi"] = ci[1]
    return summary.sort_values("dose")


def main() -> None:
    print("=" * 95)
    print("D1 raw switching: clipped (max_context=12000) vs no-clip (max_context=200000)")
    print("=" * 95)
    for obs in OBSERVABLES:
        print(f"\n--- {obs} ---")
        clipped = _switching("exp_perturb_D1_dose", obs)
        noclip = _switching("exp_perturb_D1_dose_noclip", obs)
        print(f"{'dose':>5s}  {'clipped':>22s}  {'no-clip':>22s}  {'delta':>10s}")
        print("-" * 70)
        for d in sorted(set(clipped["dose"]).intersection(set(noclip["dose"]))):
            c = clipped[clipped["dose"] == d].iloc[0]
            n = noclip[noclip["dose"] == d].iloc[0]
            delta = n["switch_rate"] - c["switch_rate"]
            cstr = f"{c['switch_rate']:.3f}[{c['ci_lo']:.2f},{c['ci_hi']:.2f}]"
            nstr = f"{n['switch_rate']:.3f}[{n['ci_lo']:.2f},{n['ci_hi']:.2f}]"
            print(f"{d:>5d}  {cstr:>22s}  {nstr:>22s}  {delta:+.3f}")


if __name__ == "__main__":
    main()
