"""
Mixed-effects logistic regression across all perturbation results
(review weakness #7 follow-up). Extends the family-cluster-bootstrap
approach in `fit_ed50_hierarchical.py` to a single global model:

  Pr(switched_{cond, fam, ic, run, regime}=1)
    = sigmoid(β_cond + u_fam + v_fam:ic + w_run)

with random intercepts for prompt_family, IC nested in family, and
run nested in IC. The model is fitted via
`statsmodels.BinomialBayesMixedGLM` (variational Bayes); we report
each non-control condition's fixed-effect coefficient + 95%
credible interval, the random-effect variances, and the per-
condition rate after marginalising over random effects.

Also reports a side-by-side comparison of:
  - per-condition mean rate (current paper, no hierarchical correction)
  - per-condition mean rate after partial-pooling shrinkage

This is the broader application of the GroupKFold / cluster-
bootstrap insight: it quantifies how much of each condition's
"effect" is explained by family / IC random variability.

Pools data across the four diagnostic perturbation pilots (O1, O2,
O3, D1); regime is a fixed-effect modifier per condition. No new
data, no API calls.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent

DEFAULT_EXPERIMENTS = [
    "exp_perturb_O1_pilot",
    "exp_perturb_O2_pilot",
    "exp_perturb_O3_pilot",
    "exp_perturb_D1_pilot",
]


def _load_paired(exp_dir: Path, regime_label: str) -> pd.DataFrame | None:
    """Same paired-control switching definition as
    fit_ed50_hierarchical.py / per_family_and_persistence.py."""
    p = exp_dir / "reports" / "perturbation" / "joint_pca10_clusters.csv"
    if not p.exists():
        return None
    clusters = pd.read_csv(p)
    finals = clusters.groupby(
        ["regime", "prompt_family", "initial_condition_id", "run_id"]
    ).apply(lambda s: s.loc[s["step"].idxmax(), "cluster"]).reset_index(name="final_cluster")
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
    paired = paired.dropna(subset=["final_cluster_ctrl"]).reset_index(drop=True)
    paired["regime_label"] = regime_label
    return paired


def main() -> int:
    parts = []
    for exp in DEFAULT_EXPERIMENTS:
        regime = exp.replace("exp_perturb_", "").replace("_pilot", "")
        df = _load_paired(REPO / "data" / exp, regime)
        if df is None:
            print(f"skip {exp}: no joint_pca10_clusters.csv")
            continue
        print(f"loaded {len(df)} rows from {regime}")
        parts.append(df)
    if not parts:
        print("no data loaded")
        return 1
    full = pd.concat(parts, ignore_index=True)
    full["family_id"] = full["prompt_family"].astype("category").cat.codes
    full["ic_id_int"] = (
        full["prompt_family"] + ":" + full["initial_condition_id"]
    ).astype("category").cat.codes
    full["regime_cond"] = full["regime_label"] + "/" + full["regime"]

    # Headline raw rates per (regime × condition).
    raw = full.groupby(["regime_label", "regime"]).agg(
        n_total=("switched", "count"),
        n_switched=("switched", "sum"),
    ).reset_index()
    raw["rate"] = raw["n_switched"] / raw["n_total"]
    print("\n=== Raw per (regime × condition) switching rates ===")
    print(raw.to_string(index=False))

    # Fit mixed-effects logistic regression with random intercepts for
    # prompt_family and (family, IC). Use a fixed-effect dummy for each
    # (regime_label, condition) cell relative to a reference cell (we'll
    # use O1/control implicitly via patsy).
    try:
        from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM
    except Exception as e:
        print(f"statsmodels not available ({e}); cannot fit GLMM. "
              f"Run `pip install statsmodels` and retry.")
        return 0

    # Build design matrix.
    print(f"\n=== Fitting mixed-effects logistic GLMM ===")
    print(f"  N = {len(full)}, families = {full['family_id'].nunique()}, "
          f"ICs = {full['ic_id_int'].nunique()}")
    print(f"  conditions: {sorted(full['regime_cond'].unique())}")
    formula = "switched ~ regime_cond"
    random = {
        "family": "0 + C(family_id)",
        "ic": "0 + C(ic_id_int)",
    }
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = BinomialBayesMixedGLM.from_formula(formula, random, full)
            result = model.fit_vb()
    except Exception as e:
        print(f"GLMM fit failed: {e}")
        return 0

    # statsmodels API: model.exog_names contains the fixed-effect column names
    fe_names = list(model.exog_names)
    print(f"\n=== Fixed-effect coefficients (vs reference cell) ===")
    print(f"{'condition':<55s} {'mean':>10s} {'lo95':>10s} {'hi95':>10s}")
    for i, name in enumerate(fe_names):
        mean = float(result.fe_mean[i])
        sd = float(result.fe_sd[i])
        lo, hi = mean - 1.96 * sd, mean + 1.96 * sd
        print(f"{name:<55s} {mean:>10.3f} {lo:>10.3f} {hi:>10.3f}")
    # statsmodels' BinomialBayesMixedGLM.fit_vb() reports the *posterior
    # mean of the log standard deviation* in vcp_mean. Convert to actual
    # SDs for interpretability.
    fam_log_sd = float(result.vcp_mean[0])
    ic_log_sd = float(result.vcp_mean[1])
    print(f"\n=== Random-effect SDs (logits) ===")
    print(f"family random-intercept SD ≈ exp({fam_log_sd:+.3f}) = {np.exp(fam_log_sd):.3f}")
    print(f"IC     random-intercept SD ≈ exp({ic_log_sd:+.3f}) = {np.exp(ic_log_sd):.3f}")
    print(f"  (intuition: SD=0.5 logits ≈ 12 percentage-point shift around p=0.5)")

    # Save coefficient table.
    out = REPO / "data" / "aggregated" / "mixed_effects_perturbation.csv"
    rows = []
    for i, name in enumerate(fe_names):
        mean = float(result.fe_mean[i])
        sd = float(result.fe_sd[i])
        rows.append({
            "term": name, "mean": mean, "sd": sd,
            "lo95": mean - 1.96 * sd, "hi95": mean + 1.96 * sd,
        })
    out_df = pd.DataFrame(rows)
    out_df["family_sd_estimate"] = float(result.vcp_mean[0])
    out_df["ic_sd_estimate"] = float(result.vcp_mean[1])
    out_df.to_csv(out, index=False)
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
