"""Multi-observable raw-switching robustness on D1 (dialog).

D1's main perturbation finding is "high raw switching at small doses"
(Fig 1, sparse pilot, plus the neutral dose sweep). This is reported on
the canonical `context_tail` observable (last 4000 chars of running
dialog transcript), with the analyzer filtering to agent turns
(`analyze.py:88-90`).

The methodological concern parallels §5.1.1: `context_tail` is a
multi-turn window observable, so high terminal-cluster switching could
be partly an averaging-of-recent-turns artefact. We re-run terminal-step
raw switching under four observables to check whether D1 saturation
holds under the cleanest single-turn observable (`last_agent_turn`),
the 3-turn agent window (`rolling_agent_k3`), and the single-step
output observable (`output`), in addition to the canonical
`context_tail`.

Pipeline per observable, on `exp_perturb_D1_dose` (D1 neutral dose
sweep, n=50 trajectories per cell, 30 steps):
  1. Load embeddings + metadata.
  2. Filter to agent turns only.
  3. Joint PCA-10 across all conditions.
  4. K-means k=12 on PCA-10.
  5. For each (regime, family, ic, run): cluster at terminal step.
  6. Raw switching = perturbed terminal cluster != control terminal cluster.

Outputs:
  data/aggregated/multi_observable_d1_raw/
    long.csv          - long-form (observable, regime, dose, switch rate, CI)
    summary.png       - 4-panel comparison: switching-vs-dose by observable.
"""
from __future__ import annotations

import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
EXP_DIR = DATA / "exp_perturb_D1_dose"
OUT_DIR = DATA / "aggregated" / "multi_observable_d1_raw"

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


def _switching_for_observable(observable: str) -> pd.DataFrame:
    print(f"\n=== {observable} ===")
    emb_path = EXP_DIR / "embeddings" / observable / "embeddings.npy"
    meta_path = EXP_DIR / "embeddings" / observable / "metadata.parquet"
    X = np.load(emb_path)
    meta = pd.read_parquet(meta_path)
    assert len(X) == len(meta), f"shape mismatch {X.shape} vs {len(meta)}"

    # Filter to agent rows only
    if "role" in meta.columns:
        keep_idx = meta["role"] == "agent"
        X = X[keep_idx.to_numpy()]
        meta = meta.loc[keep_idx].reset_index(drop=True)
        print(f"after agent-role filter: {X.shape}, {len(meta)} rows")
    else:
        print(f"loaded (no role filter): {X.shape}")

    pca = PCA(n_components=10, random_state=42)
    Xp = pca.fit_transform(X)
    print(f"joint PCA-10 explained variance: {pca.explained_variance_ratio_.sum():.3f}")
    km = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=10)
    clusters = km.fit_predict(Xp)
    df = meta.copy()
    df["cluster"] = clusters

    # Terminal-step cluster per (regime, family, ic, run)
    final_step = int(df["step"].max())
    final_rows = df[df["step"] == final_step].copy()

    # For each (family, ic, run): pull control's final cluster and
    # compare against each perturbed regime's final cluster.
    rows = []
    keys = ["prompt_family", "initial_condition_id", "run_id"]
    for (fam, ic, rid), sub in final_rows.groupby(keys):
        ctrl = sub[sub["regime"] == "control"]
        if ctrl.empty:
            continue
        ctrl_cluster = int(ctrl.iloc[0]["cluster"])
        for _, prow in sub.iterrows():
            if prow["regime"] == "control":
                continue
            rows.append({
                "observable": observable,
                "regime": prow["regime"],
                "switched": int(int(prow["cluster"]) != ctrl_cluster),
            })
    df_p = pd.DataFrame(rows)

    summary = df_p.groupby(["observable", "regime"]).agg(
        n_total=("regime", "count"),
        n_switched=("switched", "sum"),
    ).reset_index()
    summary["switch_rate"] = summary["n_switched"] / summary["n_total"]

    def _dose(s: str) -> int | None:
        m = re.match(r"neutral_dose(\d+)$", s)
        return int(m.group(1)) if m else None

    summary["dose"] = summary["regime"].map(_dose)
    ci = summary.apply(
        lambda r: _wilson_ci(r["switch_rate"], r["n_total"]), axis=1, result_type="expand"
    )
    summary["ci_lo"] = ci[0]
    summary["ci_hi"] = ci[1]
    return summary


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    parts = [_switching_for_observable(obs) for obs in OBSERVABLES]
    long = pd.concat(parts, ignore_index=True).sort_values(["observable", "dose"])
    csv_path = OUT_DIR / "long.csv"
    long.to_csv(csv_path, index=False)
    print(f"\nwrote {csv_path}")

    print("\n=== D1 neutral raw switching by observable and dose ===")
    pivot = long.pivot_table(index="dose", columns="observable", values="switch_rate")
    print(pivot.to_string(float_format=lambda x: f"{x:.3f}"))

    # 1x4 plot
    fig, axes = plt.subplots(1, 4, figsize=(16, 4.4), sharey=True)
    titles = {
        "output":           "output\n(agent generation, ~600 chars)",
        "last_agent_turn":  "last_agent_turn\n(single agent turn)",
        "rolling_agent_k3": "rolling_agent_k3\n(last 3 agent turns)",
        "context_tail":     "context_tail\n(last 4000 chars; canonical)",
    }
    for ax, obs in zip(axes, OBSERVABLES):
        sub = long[long["observable"] == obs].dropna(subset=["dose"]).sort_values("dose")
        x = sub["dose"].to_numpy()
        y = sub["switch_rate"].to_numpy()
        lo = sub["ci_lo"].to_numpy()
        hi = sub["ci_hi"].to_numpy()
        ax.errorbar(x, y, yerr=[y - lo, hi - y], fmt="o-", color="#2ca02c",
                    lw=1.8, markersize=6, capsize=3, label="raw switching")
        ax.axhline(0.5, color="grey", linestyle=":", lw=0.9, zorder=0)
        ax.set_xscale("log")
        ax.set_xticks([20, 80, 200, 400])
        ax.set_xticklabels([str(d) for d in [20, 80, 200, 400]])
        ax.set_xlabel("neutral dose (tokens)")
        ax.set_title(titles[obs], fontsize=10)
        ax.set_ylim(0, 1.02)
        ax.grid(axis="y", linestyle=":", alpha=0.4)
        if obs == "output":
            ax.set_ylabel("raw switching rate (Wilson 95% CI)")

    fig.suptitle(
        "D1 neutral dose sweep: terminal-cluster raw switching under four observables\n"
        "(K-means k=12; agent-role filtered; n=50 trajectories per dose)",
        fontsize=11,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    png_path = OUT_DIR / "summary.png"
    fig.savefig(png_path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {png_path}")


if __name__ == "__main__":
    main()
