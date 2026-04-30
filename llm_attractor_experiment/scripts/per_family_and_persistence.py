"""
Two analyses on the existing perturbation pilot data, no new API
calls. Both extend the §5.10.5–§5.10.8 line of reviewer-driven
follow-ups.

Analysis A: per-family ED50 heterogeneity
-----------------------------------------
Reports the dose-response curve *per prompt family* for the existing
O1 sparse-dose adversarial sweep. The population-level curve
saturates near 50%; the question is whether one family has a clean
barrier and another never crosses, or whether it's homogeneous
half-mixing across families.

Analysis B: persistence test
----------------------------
For each switched trajectory, check whether it *stays* in the new
basin or drifts back. Output: fraction of switched trajectories that
have a non-injection-step final cluster matching their pre-injection
basin (i.e., recovered) vs different (i.e., truly relocated).
Addresses review #2 — "is switching basin-escape or temporary
excursion?"

Inputs:
  data/exp_perturb_O1_dose_adversarial/reports/perturbation/joint_pca10_clusters.csv

Outputs:
  data/aggregated/per_family_ed50.csv
  data/aggregated/per_family_ed50.png
  data/aggregated/persistence_summary.csv
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
DOSE_REGEX = re.compile(r"^adversarial_dose(\d+)$")


def _wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = (z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def _parse_dose(c: str) -> int | None:
    m = DOSE_REGEX.match(str(c))
    return int(m.group(1)) if m else None


def _final_cluster(df: pd.DataFrame) -> pd.DataFrame:
    """Per-trajectory final-step cluster."""
    return df.groupby(
        ["regime", "prompt_family", "initial_condition_id", "run_id"]
    ).apply(lambda s: s.loc[s["step"].idxmax(), "cluster"]).reset_index(name="final_cluster")


def _build_paired(clusters: pd.DataFrame) -> pd.DataFrame:
    """Same pairing as fit_ed50_hierarchical: same-run pairing then
    fall back to control run_000."""
    finals = _final_cluster(clusters)
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
    fallback = pert[~pert.apply(
        lambda r: (r["prompt_family"], r["initial_condition_id"],
                   r["run_id"], r["regime"]) in matched, axis=1
    )]
    ctl_run0 = ctl[ctl["run_id"] == "run_000"][
        ["prompt_family", "initial_condition_id", "final_cluster"]
    ].rename(columns={"final_cluster": "final_cluster_ctrl"}).drop_duplicates(
        ["prompt_family", "initial_condition_id"]
    )
    fallback = fallback.merge(
        ctl_run0, on=["prompt_family", "initial_condition_id"], how="left",
    )
    paired = pd.concat([same_run, fallback], ignore_index=True, sort=False)
    paired["switched"] = (paired["final_cluster"] != paired["final_cluster_ctrl"]).astype(int)
    paired["dose"] = paired["regime"].map(_parse_dose)
    return paired.dropna(subset=["final_cluster_ctrl", "dose"])


def per_family_ed50(paired: pd.DataFrame, out_dir: Path) -> None:
    rows = []
    for fam, sub in paired.groupby("prompt_family"):
        for dose, sub2 in sub.groupby("dose"):
            n = len(sub2)
            k = int(sub2["switched"].sum())
            lo, hi = _wilson(k, n)
            rows.append({"family": fam, "dose": int(dose),
                         "n_total": n, "n_switched": k,
                         "rate": k / n if n else np.nan,
                         "wilson_lo": lo, "wilson_hi": hi})
    out = pd.DataFrame(rows)
    out_path = out_dir / "per_family_ed50.csv"
    out.to_csv(out_path, index=False)
    print(f"\nwrote {out_path}")
    print(out.to_string(index=False))

    families = sorted(out["family"].unique())
    fig, ax = plt.subplots(figsize=(9, 5.5), facecolor="white")
    cmap = plt.get_cmap("tab10")
    for i, fam in enumerate(families):
        s = out[out["family"] == fam].sort_values("dose")
        ax.errorbar(
            s["dose"], s["rate"],
            yerr=[s["rate"] - s["wilson_lo"], s["wilson_hi"] - s["rate"]],
            fmt="-o", color=cmap(i), label=fam, capsize=3, alpha=0.8,
        )
    pop = paired.groupby("dose").agg(rate=("switched", "mean")).reset_index()
    ax.plot(pop["dose"], pop["rate"], "--", color="black", linewidth=2.5,
            label="population (mean across families)")
    ax.axhline(0.5, color="#aaa", linestyle=":", linewidth=0.8)
    ax.set_xscale("log")
    ax.set_xlabel("adversarial dose (tokens, log scale)")
    ax.set_ylabel("switching rate")
    ax.set_title("Per-family ED50 heterogeneity\n"
                 "(does the upper-asymptote-below-1 reflect one population\n"
                 "not switching, or all families half-mixing?)")
    ax.set_facecolor("white")
    ax.set_ylim(0, 1.05)
    ax.grid(alpha=0.25, linewidth=0.5)
    ax.legend(loc="upper left", fontsize=8, framealpha=0.95)
    fig.tight_layout()
    fig_path = out_dir / "per_family_ed50.png"
    fig.savefig(fig_path, dpi=160, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {fig_path}")


def persistence_test(clusters: pd.DataFrame, out_dir: Path,
                     inject_step: int = 15) -> None:
    """For each perturbed trajectory:
      - pre_inj cluster = cluster at step inject_step - 1 (last
        pre-injection step)
      - post_inj cluster = cluster at step inject_step (immediately
        after injection)
      - final cluster = cluster at max step
      - paired control's final cluster (same family, IC, run_id;
        fallback run_000)

      Switched at injection if post_inj != pre_inj.
      Persisted if final == post_inj  (stayed in new basin)
      Recovered if final == pre_inj   (drifted back to original basin)
      Drifted_other if final ∉ {pre_inj, post_inj}  (went elsewhere)
    """
    pivot = clusters.pivot_table(
        index=["regime", "prompt_family", "initial_condition_id", "run_id"],
        columns="step", values="cluster", aggfunc="first",
    )
    pre_col = inject_step - 1
    post_col = inject_step
    final_step = clusters["step"].max()
    if pre_col not in pivot.columns or post_col not in pivot.columns or final_step not in pivot.columns:
        print(f"  required steps {pre_col}/{post_col}/{final_step} not all present")
        return
    rows = []
    for (regime, fam, ic, run), srow in pivot.iterrows():
        if regime == "control":
            continue
        pre = srow.get(pre_col)
        post = srow.get(post_col)
        end = srow.get(final_step)
        if pd.isna(pre) or pd.isna(post) or pd.isna(end):
            continue
        rows.append({
            "regime": regime, "prompt_family": fam,
            "initial_condition_id": ic, "run_id": run,
            "pre_inj_cluster": int(pre), "post_inj_cluster": int(post),
            "final_cluster": int(end),
            "kicked_at_injection": int(post != pre),
            "persisted_in_new_basin": int(end == post and post != pre),
            "drifted_back": int(end == pre and post != pre),
            "drifted_elsewhere": int(end != pre and end != post and post != pre),
        })
    df = pd.DataFrame(rows)
    if df.empty:
        print("  no perturbed trajectories with all required steps; skipping")
        return
    summary = df.groupby("regime").agg(
        n_total=("regime", "count"),
        kicked=("kicked_at_injection", "sum"),
        persisted=("persisted_in_new_basin", "sum"),
        drifted_back=("drifted_back", "sum"),
        drifted_elsewhere=("drifted_elsewhere", "sum"),
    ).reset_index()
    summary["pct_kicked"] = summary["kicked"] / summary["n_total"]
    summary["pct_persisted_given_kicked"] = (
        summary["persisted"] / summary["kicked"].replace(0, np.nan)
    )
    summary["pct_recovered_given_kicked"] = (
        summary["drifted_back"] / summary["kicked"].replace(0, np.nan)
    )
    out_path = out_dir / "persistence_summary.csv"
    summary.to_csv(out_path, index=False)
    print(f"\nwrote {out_path}")
    print(summary.to_string(index=False))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp", default="exp_perturb_O1_dose_adversarial")
    args = ap.parse_args()

    exp_dir = REPO / "data" / args.exp
    clusters_path = exp_dir / "reports" / "perturbation" / "joint_pca10_clusters.csv"
    if not clusters_path.exists():
        print(f"error: {clusters_path} not found")
        return 1
    clusters = pd.read_csv(clusters_path)
    paired = _build_paired(clusters)
    out_dir = REPO / "data" / "aggregated"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"=== Analysis A: per-family ED50 heterogeneity ===")
    per_family_ed50(paired, out_dir)
    print(f"\n=== Analysis B: persistence test (inject_step=15, max step in data) ===")
    persistence_test(clusters, out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
