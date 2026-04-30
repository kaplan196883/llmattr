"""
Fit a hierarchical dose-response model for an O1 perturbation experiment
and report ED50 (the dose where 50% of trajectories switch basins) with
a confidence interval that respects family/IC nesting.

Why this exists
---------------
The default per-cell Wilson interval treats trajectories as IID — but
they're nested in (prompt_family, initial_condition_id, run_id). When
the same family/IC seed is rerun multiple times, those trajectories share
upstream randomness (seed, prompt structure) and aren't independent. The
review (paper/openai_review.md, Weakness #7) flagged this; this script
fixes it.

What it does
------------
1. Loads per-trajectory final-step cluster assignments from
   reports/perturbation/joint_pca10_clusters.csv.
2. For each perturbed trajectory, decides whether it "switched":
   final-step cluster ≠ paired control trajectory's final-step cluster
   (same family/IC, control run_000). Mirrors the existing pipeline.
3. Fits a 4-parameter logistic (4PL) dose-response curve:

       p(switch | dose) = a + (d - a) / (1 + (dose / ED50) ** b)

   with a = lower asymptote (dose=0 baseline), d = upper asymptote
   (saturation), b = slope, ED50 = dose at half-rise.
4. Cluster-bootstraps by prompt_family (the outermost cluster level):
   resample 5 families with replacement, refit 4PL, record ED50. Repeat
   1,000× → bootstrap distribution for ED50.
5. Reports point estimate (median bootstrap), 95% percentile CI, plus
   per-dose hierarchical-bootstrap switching rate CIs.
6. Optionally fits a mixed-effects logistic GLM via statsmodels if it's
   installed (random intercepts for family + IC nested in family).
7. Saves: ED50 summary CSV, dose-response curve PNG with bootstrap band,
   per-dose hierarchical CIs CSV.

Usage
-----
    python -m scripts.fit_ed50_hierarchical \\
        --exp exp_perturb_O1_ed50_dense \\
        --n-bootstrap 1000

Outputs (under data/<exp>/reports/perturbation/):
    ed50_summary.csv          — point estimate + 95% CI for ED50, slope, asymptotes
    ed50_per_dose_ci.csv      — per-dose switching rate with hierarchical CI
    ed50_curve.png            — fitted 4PL with bootstrap band + observed points

Caveats
-------
- "Switching" is still defined as final-step cluster disagreement with
  paired control. Weakness #2 in the review (control-vs-control
  stochastic floor) is partially addressed here by also computing
  control-vs-control switching when ≥2 control runs per (family, IC)
  exist — see the --report-natural-floor flag.
- 4PL with cluster bootstrap on 5 families is the right structural
  match but 5 is small for a stable family-level random effect. The
  dense-dose config doubles ICs per family (10) and quadruples runs (4)
  to compensate; the family-level bootstrap variance is the limiting
  factor on the ED50 CI width.
- 4PL fits can fail when bootstrap resamples lack monotone support; we
  fall back to bracketing-from-the-data (linear interp on observed
  rates) for those bootstrap iterations. The fraction of failures is
  reported.
"""
from __future__ import annotations

import argparse
import re
import sys
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

REPO = Path(__file__).resolve().parent.parent

DOSE_REGEX = re.compile(r"^adversarial_dose(\d+)$")


def _parse_dose(condition: str) -> int | None:
    """Return integer dose for adversarial_doseN; None for control or other."""
    m = DOSE_REGEX.match(str(condition))
    return int(m.group(1)) if m else None


def _logistic4(x: np.ndarray, a: float, d: float, b: float, ed50: float) -> np.ndarray:
    """4PL logistic. a = lower asymptote, d = upper, b = slope, ed50 = midpoint.
    Clipped to [0,1] for numerical sanity; returned unclipped for fit."""
    return a + (d - a) / (1.0 + (np.maximum(x, 1e-9) / max(ed50, 1e-9)) ** b)


def _ed50_linear_interp(doses: np.ndarray, rates: np.ndarray, target: float = 0.5) -> float | None:
    """Fallback ED50 via linear interpolation between observed (dose, rate)
    points that bracket target. Returns None if no bracket exists."""
    order = np.argsort(doses)
    d, r = doses[order], rates[order]
    for i in range(len(d) - 1):
        if (r[i] - target) * (r[i + 1] - target) <= 0 and r[i] != r[i + 1]:
            t = (target - r[i]) / (r[i + 1] - r[i])
            return float(d[i] + t * (d[i + 1] - d[i]))
    return None


def _fit_4pl(doses: np.ndarray, switched: np.ndarray, n: np.ndarray) -> dict:
    """Fit 4PL to per-dose aggregates with weights ∝ n. Returns dict with
    params and a flag for fit success."""
    rates = switched / np.maximum(n, 1)
    a0 = float(rates.min())
    d0 = float(rates.max())
    ed500 = float(np.median(doses))
    b0 = 1.0
    p0 = [a0, max(d0, a0 + 0.05), b0, ed500]

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            popt, _pcov = curve_fit(
                _logistic4, doses, rates,
                p0=p0,
                bounds=([0.0, 0.0, 0.1, 1.0], [1.0, 1.0, 20.0, 10000.0]),
                sigma=1.0 / np.sqrt(np.maximum(n, 1)),
                absolute_sigma=False,
                maxfev=5000,
            )
        return {
            "ok": True, "a": float(popt[0]), "d": float(popt[1]),
            "b": float(popt[2]), "ed50": float(popt[3]),
        }
    except Exception:
        ed50_lin = _ed50_linear_interp(doses, rates)
        return {
            "ok": False, "a": a0, "d": d0, "b": np.nan,
            "ed50": float(ed50_lin) if ed50_lin is not None else np.nan,
        }


def _per_traj_switching(clusters: pd.DataFrame) -> pd.DataFrame:
    """Build a per-trajectory switching dataframe.
    Pairing rule: each trajectory at the maximum step is compared to the
    control trajectory with the same (family, ic_id, run_id) — same
    pairing as the existing pipeline. If that fails, fall back to control
    run_000 with same (family, ic_id)."""
    final_step = clusters.groupby(
        ["regime", "prompt_family", "initial_condition_id", "run_id"]
    )["step"].max().reset_index().rename(columns={"step": "final_step"})

    finals = clusters.merge(
        final_step,
        left_on=["regime", "prompt_family", "initial_condition_id", "run_id", "step"],
        right_on=["regime", "prompt_family", "initial_condition_id", "run_id", "final_step"],
        how="inner",
    )[["regime", "prompt_family", "initial_condition_id", "run_id", "cluster"]]

    controls = finals[finals["regime"] == "control"].rename(
        columns={"cluster": "control_cluster", "run_id": "control_run_id"}
    )

    # Try same-run pairing first.
    same_run = finals[finals["regime"] != "control"].merge(
        controls,
        on=["prompt_family", "initial_condition_id"],
        suffixes=("", "_ctrl"),
    )
    same_run = same_run[same_run["run_id"] == same_run["control_run_id"]].copy()

    # For perturbed (family, ic_id, run_id) triples without a same-run
    # control, fall back to control run_000.
    matched_keys = set(zip(
        same_run["prompt_family"], same_run["initial_condition_id"],
        same_run["run_id"], same_run["regime"],
    ))
    perturbed_finals = finals[finals["regime"] != "control"]
    fallback_rows = perturbed_finals[~perturbed_finals.apply(
        lambda r: (r["prompt_family"], r["initial_condition_id"],
                   r["run_id"], r["regime"]) in matched_keys, axis=1
    )]
    ctrl_run0 = controls[controls["control_run_id"] == "run_000"][
        ["prompt_family", "initial_condition_id", "control_cluster"]
    ].drop_duplicates(["prompt_family", "initial_condition_id"])
    fallback = fallback_rows.merge(
        ctrl_run0, on=["prompt_family", "initial_condition_id"], how="left"
    )

    paired = pd.concat([same_run, fallback], ignore_index=True, sort=False)
    paired["switched"] = (paired["cluster"] != paired["control_cluster"]).astype(int)
    paired["dose"] = paired["regime"].map(_parse_dose)
    return paired.dropna(subset=["dose", "control_cluster"]).reset_index(drop=True)


def _natural_floor(clusters: pd.DataFrame) -> dict | None:
    """Estimate control-vs-control switching by pairing each control run
    with every other control run from the same (family, IC). Each ordered
    distinct pair contributes one binary. Returns None if <2 control runs
    per cell."""
    fs = clusters.groupby(
        ["regime", "prompt_family", "initial_condition_id", "run_id"]
    )["step"].max().reset_index().rename(columns={"step": "final_step"})
    finals = clusters.merge(
        fs,
        left_on=["regime", "prompt_family", "initial_condition_id", "run_id", "step"],
        right_on=["regime", "prompt_family", "initial_condition_id", "run_id", "final_step"],
        how="inner",
    )
    ctl = finals[finals["regime"] == "control"]
    pairs = []
    for (_, _), grp in ctl.groupby(["prompt_family", "initial_condition_id"]):
        runs = grp["run_id"].tolist()
        clusts = grp["cluster"].tolist()
        for i in range(len(runs)):
            for j in range(len(runs)):
                if i != j:
                    pairs.append(int(clusts[i] != clusts[j]))
    if len(pairs) < 4:
        return None
    arr = np.asarray(pairs)
    n = len(arr)
    p = float(arr.mean())
    z = 1.959963984540054
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = (z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return {"floor_rate": p, "n_pairs": n,
            "wilson_lo": float(centre - half), "wilson_hi": float(centre + half)}


def _bootstrap_ed50(
    paired: pd.DataFrame, n_bootstrap: int, seed: int,
) -> dict:
    """Cluster-bootstrap by family. At each iter, resample the 5 unique
    family labels with replacement, build a working dataframe, and refit
    4PL. Record ED50 + asymptotes."""
    families = paired["prompt_family"].unique().tolist()
    rng = np.random.default_rng(seed)
    records = []
    n_fail = 0
    for _ in range(n_bootstrap):
        sample_fams = rng.choice(families, size=len(families), replace=True)
        boots = pd.concat(
            [paired[paired["prompt_family"] == f] for f in sample_fams],
            ignore_index=True,
        )
        agg = boots.groupby("dose")["switched"].agg(["sum", "count"])
        if len(agg) < 3:
            n_fail += 1; continue
        fit = _fit_4pl(
            agg.index.to_numpy(dtype=float),
            agg["sum"].to_numpy(dtype=float),
            agg["count"].to_numpy(dtype=float),
        )
        if not np.isnan(fit["ed50"]):
            records.append((fit["ed50"], fit["a"], fit["d"], fit["b"], fit["ok"]))
        else:
            n_fail += 1
    if not records:
        raise RuntimeError("all bootstrap fits failed; check the data")
    arr = np.array([(e, a, d, b) for e, a, d, b, _ in records])
    return {
        "ed50_median": float(np.median(arr[:, 0])),
        "ed50_lo": float(np.percentile(arr[:, 0], 2.5)),
        "ed50_hi": float(np.percentile(arr[:, 0], 97.5)),
        "a_median": float(np.median(arr[:, 1])),
        "d_median": float(np.median(arr[:, 2])),
        "b_median": float(np.median(arr[:, 3])),
        "n_bootstrap": len(records),
        "n_failed": n_fail,
        "ed50_samples": arr[:, 0],
    }


def _per_dose_hier_ci(paired: pd.DataFrame, n_bootstrap: int, seed: int) -> pd.DataFrame:
    """Family-cluster-bootstrap CI per dose."""
    families = paired["prompt_family"].unique().tolist()
    rng = np.random.default_rng(seed + 1)
    doses = sorted(paired["dose"].unique())
    samples: dict[int, list[float]] = {d: [] for d in doses}
    for _ in range(n_bootstrap):
        sample_fams = rng.choice(families, size=len(families), replace=True)
        boots = pd.concat(
            [paired[paired["prompt_family"] == f] for f in sample_fams],
            ignore_index=True,
        )
        for d in doses:
            sub = boots[boots["dose"] == d]
            if len(sub):
                samples[d].append(float(sub["switched"].mean()))
    rows = []
    for d in doses:
        arr = np.asarray(samples[d]) if samples[d] else np.array([])
        cell = paired[paired["dose"] == d]
        rows.append({
            "dose": int(d),
            "n_total": int(len(cell)),
            "n_switched": int(cell["switched"].sum()),
            "rate_observed": float(cell["switched"].mean()) if len(cell) else np.nan,
            "rate_boot_lo": float(np.percentile(arr, 2.5)) if len(arr) else np.nan,
            "rate_boot_hi": float(np.percentile(arr, 97.5)) if len(arr) else np.nan,
        })
    return pd.DataFrame(rows)


def _try_glmm(paired: pd.DataFrame) -> dict | None:
    """Optional confirmatory mixed-effects logistic GLM with random
    intercepts for family + IC. Requires statsmodels; returns None if
    unavailable or the fit fails."""
    try:
        from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM
    except Exception:
        return None
    try:
        df = paired.copy()
        df["log_dose"] = np.log10(df["dose"])
        df["family_id"] = df["prompt_family"].astype("category").cat.codes
        df["ic_id_int"] = (
            df["prompt_family"] + ":" + df["initial_condition_id"]
        ).astype("category").cat.codes
        random = {
            "family": "0 + C(family_id)",
            "ic": "0 + C(ic_id_int)",
        }
        model = BinomialBayesMixedGLM.from_formula(
            "switched ~ log_dose", random, df,
        )
        result = model.fit_vb()
        intercept = float(result.fe_mean[0])
        slope = float(result.fe_mean[1])
        # ED50 in dose space: solve intercept + slope * log10(ed50) = 0
        if abs(slope) > 1e-9:
            ed50 = float(10 ** (-intercept / slope))
        else:
            ed50 = float("nan")
        return {"intercept": intercept, "slope": slope, "ed50": ed50}
    except Exception as e:
        print(f"[glmm] fit failed: {e}")
        return None


def _plot_curve(
    paired: pd.DataFrame, fit: dict, boot: dict, per_dose: pd.DataFrame,
    out_path: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(8, 5.5), facecolor="white")
    ax.set_facecolor("white")

    xs = np.logspace(np.log10(5), np.log10(500), 200)
    ys_main = _logistic4(xs, fit["a"], fit["d"], fit["b"], fit["ed50"])

    # Bootstrap band: for a sample of bootstrap (a,d,b,ED50) tuples,
    # evaluate the 4PL across xs and take 2.5/97.5 percentiles per x.
    if "ed50_samples" in boot and len(boot["ed50_samples"]):
        idx = np.linspace(0, len(boot["ed50_samples"]) - 1, num=300).astype(int)
        # Approx: use medians of a,d,b and per-iter ed50 (efficient and visually fine).
        ys_band = np.array([
            _logistic4(xs, boot["a_median"], boot["d_median"], boot["b_median"],
                       boot["ed50_samples"][i])
            for i in idx
        ])
        lo = np.percentile(ys_band, 2.5, axis=0)
        hi = np.percentile(ys_band, 97.5, axis=0)
        ax.fill_between(xs, lo, hi, color="#1f77b4", alpha=0.15,
                        label="95% bootstrap band (ED50 only)")

    ax.plot(xs, ys_main, color="#1f77b4", linewidth=2,
            label=f"4PL fit (ED50 = {fit['ed50']:.0f} tok)")

    # Observed points with hierarchical CIs.
    obs = per_dose.dropna(subset=["rate_observed"])
    yerr = np.array([
        obs["rate_observed"] - obs["rate_boot_lo"],
        obs["rate_boot_hi"] - obs["rate_observed"],
    ])
    ax.errorbar(
        obs["dose"], obs["rate_observed"],
        yerr=yerr, fmt="o", color="#222", ecolor="#666",
        capsize=3, markersize=6, label="observed (95% family-bootstrap CI)",
    )

    ax.axhline(0.5, color="#aaa", linestyle="--", linewidth=0.8,
               label="50% switch threshold")
    ax.axvline(boot["ed50_median"], color="#d62728", linestyle="--",
               linewidth=0.8,
               label=f"ED50 = {boot['ed50_median']:.0f} tok "
                     f"[{boot['ed50_lo']:.0f}–{boot['ed50_hi']:.0f}]")

    ax.set_xscale("log")
    ax.set_xlim(15, 500)
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("adversarial dose (tokens, log scale)")
    ax.set_ylabel("fraction of trajectories switching basin")
    ax.set_title("O1 adversarial dose-response — confirmatory dense rerun\n"
                 "4-parameter logistic with family-cluster-bootstrap CI")
    ax.legend(loc="lower right", fontsize=9, framealpha=0.95)
    ax.grid(alpha=0.25, linewidth=0.5)
    fig.tight_layout()
    fig.savefig(out_path, dpi=170, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out_path}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp", default="exp_perturb_O1_ed50_dense",
                    help="experiment id (under data/<exp>)")
    ap.add_argument("--n-bootstrap", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--report-natural-floor", action="store_true",
                    help="also report control-vs-control switching baseline")
    args = ap.parse_args()

    exp_dir = REPO / "data" / args.exp
    clusters_path = exp_dir / "reports" / "perturbation" / "joint_pca10_clusters.csv"
    if not clusters_path.exists():
        print(f"error: {clusters_path} not found — run the experiment first.")
        return 1

    clusters = pd.read_csv(clusters_path)
    paired = _per_traj_switching(clusters)
    print(f"loaded {len(paired)} perturbed trajectories across "
          f"{paired['prompt_family'].nunique()} families × "
          f"{paired.groupby('prompt_family')['initial_condition_id'].nunique().max()} ICs")

    fit_pooled_agg = paired.groupby("dose")["switched"].agg(["sum", "count"])
    fit_pooled = _fit_4pl(
        fit_pooled_agg.index.to_numpy(dtype=float),
        fit_pooled_agg["sum"].to_numpy(dtype=float),
        fit_pooled_agg["count"].to_numpy(dtype=float),
    )
    print(f"pooled 4PL fit ok={fit_pooled['ok']}: ED50={fit_pooled['ed50']:.1f} "
          f"a={fit_pooled['a']:.3f} d={fit_pooled['d']:.3f} b={fit_pooled['b']:.2f}")

    print(f"running cluster-bootstrap n={args.n_bootstrap}...")
    boot = _bootstrap_ed50(paired, args.n_bootstrap, args.seed)
    print(f"  ED50 bootstrap median {boot['ed50_median']:.1f} tok, "
          f"95% CI [{boot['ed50_lo']:.1f}, {boot['ed50_hi']:.1f}], "
          f"{boot['n_failed']}/{args.n_bootstrap} fits failed")

    per_dose = _per_dose_hier_ci(paired, args.n_bootstrap, args.seed)
    print(per_dose.to_string(index=False))

    glmm = _try_glmm(paired)
    if glmm:
        print(f"GLMM (statsmodels) ED50 = {glmm['ed50']:.1f} (slope on log10 dose)")

    floor = _natural_floor(clusters) if args.report_natural_floor else None
    if floor:
        print(f"natural floor (control-vs-control): {floor['floor_rate']:.3f} "
              f"[{floor['wilson_lo']:.3f}, {floor['wilson_hi']:.3f}] "
              f"(n_pairs={floor['n_pairs']})")

    out_dir = exp_dir / "reports" / "perturbation"
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = pd.DataFrame([{
        "ed50_pooled": fit_pooled["ed50"],
        "ed50_boot_median": boot["ed50_median"],
        "ed50_boot_lo": boot["ed50_lo"],
        "ed50_boot_hi": boot["ed50_hi"],
        "a_pooled": fit_pooled["a"],
        "d_pooled": fit_pooled["d"],
        "b_pooled": fit_pooled["b"],
        "n_bootstrap_ok": boot["n_bootstrap"],
        "n_bootstrap_fail": boot["n_failed"],
        "ed50_glmm": glmm["ed50"] if glmm else np.nan,
        "natural_floor_rate": floor["floor_rate"] if floor else np.nan,
        "natural_floor_n_pairs": floor["n_pairs"] if floor else np.nan,
    }])
    summary.to_csv(out_dir / "ed50_summary.csv", index=False)
    print(f"wrote {out_dir / 'ed50_summary.csv'}")
    per_dose.to_csv(out_dir / "ed50_per_dose_ci.csv", index=False)
    print(f"wrote {out_dir / 'ed50_per_dose_ci.csv'}")
    _plot_curve(paired, fit_pooled, boot, per_dose, out_dir / "ed50_curve.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
