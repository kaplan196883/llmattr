"""Full no-clip persistence dose-response curve, doses 20-3000.

Combines:
  - exp_perturb_O1_ed50_dense_noclip (n=200/cell, doses 20, 50, 80, 120, 160, 200, 300, 400)
  - exp_perturb_O1_ed50_higher_noclip (n=100/cell, doses 600, 1000, 1500, 2000, 3000)

Outputs:
  data/aggregated/multi_observable_persistence_full_noclip/
    long.csv     - per (observable, dose) row
    plot.png     - 3-panel comparison: clipped vs no-clip vs higher-dose-noclip
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
OUT_DIR = DATA / "aggregated" / "multi_observable_persistence_full_noclip"

DENSE_NOCLIP = "exp_perturb_O1_ed50_dense_noclip"
HIGHER_NOCLIP = "exp_perturb_O1_ed50_higher_noclip"
DENSE_CLIPPED = "exp_perturb_O1_ed50_dense"

OBSERVABLES = ["output", "rolling_k3", "context_tail"]
N_CLUSTERS = 12


def _wilson_ci(p, n):
    if n == 0:
        return (float("nan"), float("nan"))
    z = 1.959963984540054
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def _persistence(exp_name, observable):
    exp_dir = DATA / exp_name
    X = np.load(exp_dir / "embeddings" / observable / "embeddings.npy")
    meta = pd.read_parquet(exp_dir / "embeddings" / observable / "metadata.parquet")
    pca = PCA(n_components=10, random_state=42)
    Xp = pca.fit_transform(X)
    km = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=10)
    df = meta.copy()
    df["cluster"] = km.fit_predict(Xp)
    pivot = df.pivot_table(
        index=["regime", "prompt_family", "initial_condition_id", "run_id"],
        columns="step", values="cluster", aggfunc="first",
    )
    final_step = int(df["step"].max())
    needed = (14, 15, final_step)
    if not all(c in pivot.columns for c in needed):
        return pd.DataFrame()
    rows = []
    for (regime, fam, ic, run), srow in pivot.iterrows():
        if regime == "control":
            continue
        pre, post, end = srow.get(14), srow.get(15), srow.get(final_step)
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


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    parts = []
    for exp in [DENSE_CLIPPED, DENSE_NOCLIP, HIGHER_NOCLIP]:
        for obs in OBSERVABLES:
            print(f"computing {exp} / {obs} ...")
            parts.append(_persistence(exp, obs))
    long = pd.concat(parts, ignore_index=True)
    csv_path = OUT_DIR / "long.csv"
    long.to_csv(csv_path, index=False)
    print(f"\nwrote {csv_path}")

    # Print summary table
    print("\n=== Persistence: clipped vs no-clip across all tested doses ===")
    print(f"{'dose':>5s} {'observable':>14s} {'clipped':>20s} {'no-clip':>20s}")
    for obs in OBSERVABLES:
        clipped = long[(long["experiment"] == DENSE_CLIPPED) & (long["observable"] == obs)]
        noclip_dense = long[(long["experiment"] == DENSE_NOCLIP) & (long["observable"] == obs)]
        noclip_higher = long[(long["experiment"] == HIGHER_NOCLIP) & (long["observable"] == obs)]
        all_doses = sorted(set(clipped["dose"]).union(set(noclip_dense["dose"])).union(set(noclip_higher["dose"])))
        for d in all_doses:
            clip_row = clipped[clipped["dose"] == d]
            cstr = "-"
            if not clip_row.empty:
                r = clip_row.iloc[0]
                cstr = f"{r['pct_persisted']:.3f} [{r['persisted_ci_lo']:.2f},{r['persisted_ci_hi']:.2f}]"
            nc_row = pd.concat([noclip_dense[noclip_dense["dose"] == d],
                                noclip_higher[noclip_higher["dose"] == d]])
            ncstr = "-"
            if not nc_row.empty:
                r = nc_row.iloc[0]
                ncstr = f"{r['pct_persisted']:.3f} [{r['persisted_ci_lo']:.2f},{r['persisted_ci_hi']:.2f}]"
            print(f"{d:>5d} {obs:>14s} {cstr:>20s} {ncstr:>20s}")

    # Plot: 3-panel, one per observable, showing clipped + merged full-history curves.
    # The two full-history experiments (DENSE_NOCLIP doses 20-400 at n=200 and
    # HIGHER_NOCLIP doses 600-3000 at n=100) share an identical no-clip protocol;
    # only the per-cell N differs, so we plot them as a single continuous series
    # to match the Fig 1 panel B treatment in scripts/build_fig1_panels.py.
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)
    for ax, obs in zip(axes, OBSERVABLES):
        # Bounded-memory clipped baseline
        sub_clip = long[(long["experiment"] == DENSE_CLIPPED) &
                        (long["observable"] == obs)].dropna(subset=["dose"]).sort_values("dose")
        if not sub_clip.empty:
            x = sub_clip["dose"].to_numpy()
            y = sub_clip["pct_persisted"].to_numpy()
            lo = sub_clip["persisted_ci_lo"].to_numpy()
            hi = sub_clip["persisted_ci_hi"].to_numpy()
            ax.errorbar(x, y, yerr=[y - lo, hi - y], fmt="s-",
                        color="#1f77b4", lw=1.5, markersize=5, capsize=3,
                        label="clipped (max_context=12K)")
        # Full-history merged across the two no-clip experiments.
        sub_fh = long[(long["experiment"].isin([DENSE_NOCLIP, HIGHER_NOCLIP])) &
                      (long["observable"] == obs)].dropna(subset=["dose"]).sort_values("dose")
        if not sub_fh.empty:
            x = sub_fh["dose"].to_numpy()
            y = sub_fh["pct_persisted"].to_numpy()
            lo = sub_fh["persisted_ci_lo"].to_numpy()
            hi = sub_fh["persisted_ci_hi"].to_numpy()
            ax.errorbar(x, y, yerr=[y - lo, hi - y], fmt="o-",
                        color="#d62728", lw=1.5, markersize=5, capsize=3,
                        label="full-history (max_context=200K)")
        ax.axhline(0.5, color="grey", linestyle=":", lw=0.9, zorder=0,
                   label="50% half-effect threshold" if obs == "output" else None)
        ax.set_xscale("log")
        ax.set_xticks([20, 50, 100, 200, 400, 1000, 2000, 3000])
        ax.set_xticklabels(["20", "50", "100", "200", "400", "1000", "2000", "3000"])
        ax.set_xlabel("adversarial dose (tokens)")
        ax.set_ylim(0, 1.0)
        ax.grid(axis="y", linestyle=":", alpha=0.4)
        ax.set_title(f"observable: {obs}", fontsize=11)
        if obs == "output":
            ax.set_ylabel("persistent-escape rate (Wilson 95% CI)")
        ax.legend(fontsize=8, loc="upper left")
    fig.suptitle(
        "O1 append-mode persistence dose response: clipped vs no-clip across 5-3000 tokens",
        fontsize=12,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    png_path = OUT_DIR / "plot.png"
    fig.savefig(png_path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {png_path}")


if __name__ == "__main__":
    main()
