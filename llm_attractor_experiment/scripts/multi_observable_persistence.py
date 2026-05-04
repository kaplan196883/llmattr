"""Multi-observable persistence on the O1 dense rerun.

Re-runs the kicked / persisted / drifted_* analysis under three text
observables (`output`, `rolling_k3`, `context_tail`) so the persistent
escape claim can be scoped against observable choice.

Pipeline per observable:
  1. Load embeddings + metadata.
  2. Joint PCA-10 across all conditions (matches the canonical analyzer).
  3. K-means k=12 on the joint PCA-10.
  4. For each (regime, family, ic, run): cluster at pre (step 14), post
     (step 15), final (step 29). Persisted iff post != pre AND final == post.
  5. Aggregate by regime; compute persistence rate per dose.

Outputs:
  data/aggregated/multi_observable_persistence/
    long.csv           — long-form (observable, regime, dose, kicked, persisted, ...)
    summary.png        — 3-panel comparison: persistence-vs-dose by observable.

Run:
  python -m scripts.multi_observable_persistence
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
EXP_DIR = DATA / "exp_perturb_O1_ed50_dense"
OUT_DIR = DATA / "aggregated" / "multi_observable_persistence"

OBSERVABLES = ["output", "rolling_k3", "context_tail"]
N_CLUSTERS = 12
INJECT_STEP = 15
PRE_STEP = INJECT_STEP - 1


def _wilson_ci(p: float, n: int) -> tuple[float, float]:
    """Wilson 95% CI for a binomial proportion."""
    if n == 0:
        return (float("nan"), float("nan"))
    z = 1.959963984540054
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def _persistence_for_observable(observable: str) -> pd.DataFrame:
    print(f"\n=== {observable} ===")
    emb_path = EXP_DIR / "embeddings" / observable / "embeddings.npy"
    meta_path = EXP_DIR / "embeddings" / observable / "metadata.parquet"
    X = np.load(emb_path)
    meta = pd.read_parquet(meta_path)
    assert len(X) == len(meta), f"shape mismatch {X.shape} vs {len(meta)}"

    print(f"loaded {X.shape}, {len(meta)} rows")

    # Joint PCA-10 + K-means k=12 (matches canonical analyzer)
    pca = PCA(n_components=10, random_state=42)
    Xp = pca.fit_transform(X)
    print(f"joint PCA-10 explained variance: {pca.explained_variance_ratio_.sum():.3f}")
    km = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=10)
    clusters = km.fit_predict(Xp)
    df = meta.copy()
    df["cluster"] = clusters

    # Pivot per (regime, family, ic, run) over step
    pivot = df.pivot_table(
        index=["regime", "prompt_family", "initial_condition_id", "run_id"],
        columns="step", values="cluster", aggfunc="first",
    )
    final_step = int(df["step"].max())
    needed = (PRE_STEP, INJECT_STEP, final_step)
    if not all(c in pivot.columns for c in needed):
        raise RuntimeError(f"missing one of needed steps {needed} in pivot")

    rows = []
    for (regime, fam, ic, run), srow in pivot.iterrows():
        if regime == "control":
            continue
        pre, post, end = srow.get(PRE_STEP), srow.get(INJECT_STEP), srow.get(final_step)
        if pd.isna(pre) or pd.isna(post) or pd.isna(end):
            continue
        rows.append({
            "observable": observable,
            "regime": regime,
            "kicked": int(post != pre),
            "persisted": int(end == post and post != pre),
            "drifted_back": int(end == pre and post != pre),
            "drifted_elsewhere": int(end != pre and end != post and post != pre),
        })
    df_p = pd.DataFrame(rows)

    summary = df_p.groupby(["observable", "regime"]).agg(
        n_total=("regime", "count"),
        kicked=("kicked", "sum"),
        persisted=("persisted", "sum"),
        drifted_back=("drifted_back", "sum"),
        drifted_elsewhere=("drifted_elsewhere", "sum"),
    ).reset_index()

    # Extract dose from regime name like 'adversarial_dose200'
    def _dose(s: str) -> int | None:
        m = re.match(r"adversarial_dose(\d+)$", s)
        return int(m.group(1)) if m else None

    summary["dose"] = summary["regime"].map(_dose)
    summary["pct_kicked"] = summary["kicked"] / summary["n_total"]
    summary["pct_persisted"] = summary["persisted"] / summary["n_total"]
    summary["pct_drifted_back"] = summary["drifted_back"] / summary["n_total"]
    summary["pct_drifted_elsewhere"] = summary["drifted_elsewhere"] / summary["n_total"]

    # Wilson CI for persistence rate
    ci = summary.apply(
        lambda r: _wilson_ci(r["pct_persisted"], r["n_total"]), axis=1, result_type="expand"
    )
    summary["persisted_ci_lo"] = ci[0]
    summary["persisted_ci_hi"] = ci[1]

    return summary


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    parts = [_persistence_for_observable(obs) for obs in OBSERVABLES]
    long = pd.concat(parts, ignore_index=True)
    long = long.sort_values(["observable", "dose"])

    csv_path = OUT_DIR / "long.csv"
    long.to_csv(csv_path, index=False)
    print(f"\nwrote {csv_path}")

    # Print summary table
    print("\n=== Persistence rates at dose 200 and 400 ===")
    for obs in OBSERVABLES:
        sub = long[long["observable"] == obs]
        for dose in (200, 400):
            r = sub[sub["dose"] == dose]
            if r.empty:
                continue
            row = r.iloc[0]
            print(f"  {obs:14s} d={dose:4d}  persisted={row['pct_persisted']:.3f}"
                  f"  [{row['persisted_ci_lo']:.3f}, {row['persisted_ci_hi']:.3f}]"
                  f"  (n={int(row['n_total'])})")

    # Plot: 3-panel comparison
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.4), sharey=True)
    obs_titles = {
        "output":       "output\n(single-step generation)",
        "rolling_k3":   "rolling_k3\n(last 3 outputs)",
        "context_tail": "context_tail\n(last 4000 chars; canonical)",
    }
    for ax, obs in zip(axes, OBSERVABLES):
        sub = long[long["observable"] == obs].dropna(subset=["dose"]).sort_values("dose")
        x = sub["dose"].to_numpy()
        y = sub["pct_persisted"].to_numpy()
        lo = sub["persisted_ci_lo"].to_numpy()
        hi = sub["persisted_ci_hi"].to_numpy()
        ax.errorbar(
            x, y, yerr=[y - lo, hi - y],
            fmt="o-", color="#d62728", lw=1.8, markersize=6, capsize=3,
            label="persistent escape",
        )
        # Also plot kicked-at-injection for reference
        ax.plot(x, sub["pct_kicked"], "s--", color="#7f7f7f", lw=1.2,
                markersize=4, alpha=0.7, label="kicked at injection")
        ax.axhline(0.5, color="grey", linestyle=":", lw=0.9, zorder=0)
        ax.set_xscale("log")
        ax.set_xticks([20, 50, 80, 120, 160, 200, 300, 400])
        ax.set_xticklabels([str(d) for d in [20, 50, 80, 120, 160, 200, 300, 400]])
        ax.set_xlabel("adversarial dose (tokens)")
        ax.set_title(obs_titles[obs], fontsize=10)
        ax.set_ylim(0, 1.02)
        ax.grid(axis="y", linestyle=":", alpha=0.4)
        if obs == "output":
            ax.set_ylabel("rate (Wilson 95% CI for persistent escape)")
        ax.legend(fontsize=8, loc="upper left")

    fig.suptitle(
        "O1 adversarial dense rerun: persistence-vs-dose under three text observables\n"
        "(K-means k=12; persisted = jumped at injection AND in post-injection cluster at terminal step)",
        fontsize=11,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    png_path = OUT_DIR / "summary.png"
    fig.savefig(png_path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {png_path}")


if __name__ == "__main__":
    main()
