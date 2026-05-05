"""Experiment A — zero-cost dip-mechanism sweep on existing trajectories.

Tests whether the high-dose destination-coherent persistence dip
(S^dst at 1500/2000/3000 = 0.51/0.32/0.41 under canonical context_tail
+ K-means k=12) survives:

  V1  endpoint redefinition: C_+ taken from output / rolling_k3 / context_tail
      at injection step 15 vs steps 16-18 (lets the model "settle" before
      the destination cluster is fixed).
  V2  cluster granularity: k in {3, 6, 8, 12, 18, 24, 32}.
  V3  time-integrated terminal: fraction of steps 25-29 in C_+ instead of
      strict label retention at the single terminal step.
  V4  transition entropy H(C_T | C_+) by dose: does dose 2000 uniquely
      maximize post-kick destination scatter?

Falsification logic:
  - If the dip vanishes under any single transformation -> that mechanism
    is supported (most likely V1: endpoint mismatch between raw-injection
    cluster vs generated-continuation cluster).
  - If the dip survives all transformations -> mechanism 1, 2 are ruled
    out and we move to Experiment B (long-horizon relaxation).

Output: data/aggregated/dip_mechanism_A/
  table.csv   - per (variant, observable, k, definition, dose) row with
                S^dst, kicked, source-escape, transition entropy.
  summary.md  - dip-magnitude table: Delta = S(2000) - mean(S(1500),S(3000))
                under each setup. Sign and magnitude verdict per mechanism.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT_DIR = DATA / "aggregated" / "dip_mechanism_A"

EXP_LOW = "exp_perturb_O1_ed50_dense_noclip"      # n=200, doses 20-400
EXP_HIGH = "exp_perturb_O1_ed50_higher_noclip"    # n=100, doses 600-3000

OBSERVABLES = ["output", "rolling_k3", "context_tail"]
K_GRID = [3, 6, 8, 12, 18, 24, 32]
INJECT_STEP = 15
PRE_STEP = INJECT_STEP - 1
FINAL_STEP_DEFAULT = 29
LATE_WINDOW = (25, 29)  # for time-integrated variant V3


def _wilson(p: float, n: int) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    z = 1.959963984540054
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def _dose(regime: str) -> int | None:
    m = re.match(r"adversarial_dose(\d+)$", regime)
    return int(m.group(1)) if m else None


def _load_single(exp: str, observable: str) -> tuple[np.ndarray, pd.DataFrame]:
    X = np.load(DATA / exp / "embeddings" / observable / "embeddings.npy")
    meta = pd.read_parquet(DATA / exp / "embeddings" / observable / "metadata.parquet")
    return X, meta.assign(experiment=exp)


def _load_combined(observable: str) -> tuple[np.ndarray, pd.DataFrame]:
    """Stack the two no-clip experiments into one (regime,fam,ic,run,step) table."""
    parts_X, parts_meta = [], []
    for exp in (EXP_LOW, EXP_HIGH):
        X, meta = _load_single(exp, observable)
        parts_X.append(X)
        parts_meta.append(meta)
    return np.vstack(parts_X), pd.concat(parts_meta, ignore_index=True)


def _cluster(X: np.ndarray, k: int) -> np.ndarray:
    pca = PCA(n_components=10, random_state=42)
    Xp = pca.fit_transform(X)
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    return km.fit_predict(Xp)


def _persistence_table(
    observable: str,
    k: int,
    plus_step: int,
    final_step: int = FINAL_STEP_DEFAULT,
    *,
    time_integrated_window: tuple[int, int] | None = None,
    fit_scope: str = "per_experiment",
) -> pd.DataFrame:
    """Compute kicked / destination-coherent / source-escape per dose.

    plus_step: step at which C_+ is recorded (canonical: 15; delayed
        variants: 16-18).
    time_integrated_window: if given, the strict endpoint becomes
        `fraction of steps in [t0, t1] equal to C_+` rather than
        C_T == C_+ at the single terminal step.
    fit_scope: "per_experiment" (matches the paper: cluster each
        experiment alone, then concat) or "joint" (fit PCA+K-means
        across both experiments combined).
    """
    if fit_scope == "joint":
        X, meta = _load_combined(observable)
        df = meta.copy()
        df["cluster"] = _cluster(X, k)
    elif fit_scope == "per_experiment":
        parts = []
        for exp in (EXP_LOW, EXP_HIGH):
            X, meta = _load_single(exp, observable)
            sub = meta.copy()
            sub["cluster"] = _cluster(X, k)
            # disambiguate cluster ids per experiment by experiment-prefix
            sub["cluster"] = sub["experiment"] + "_c" + sub["cluster"].astype(str)
            parts.append(sub)
        df = pd.concat(parts, ignore_index=True)
    else:
        raise ValueError(f"unknown fit_scope: {fit_scope}")
    pivot = df.pivot_table(
        index=["regime", "prompt_family", "initial_condition_id", "run_id"],
        columns="step", values="cluster", aggfunc="first",
    )
    rows = []
    for (regime, fam, ic, run), srow in pivot.iterrows():
        if regime == "control":
            continue
        pre = srow.get(PRE_STEP)
        post = srow.get(plus_step)
        end = srow.get(final_step)
        if pd.isna(pre) or pd.isna(post) or pd.isna(end):
            continue
        kicked = int(post != pre)
        if time_integrated_window is None:
            destcoh = int(end == post and post != pre)
        else:
            t0, t1 = time_integrated_window
            window = [srow.get(t) for t in range(t0, t1 + 1)]
            window = [c for c in window if not pd.isna(c)]
            frac_in_post = (np.array(window) == post).mean() if window else float("nan")
            destcoh = int(frac_in_post >= 0.5 and post != pre)
        srcesc = int(end != pre and post != pre)
        rows.append({
            "regime": regime,
            "kicked": kicked,
            "destcoh": destcoh,
            "srcesc": srcesc,
            "post_cluster": post,
            "end_cluster": end,
        })
    df_p = pd.DataFrame(rows)
    summary = df_p.groupby("regime").agg(
        n=("regime", "count"),
        kicked=("kicked", "sum"),
        destcoh=("destcoh", "sum"),
        srcesc=("srcesc", "sum"),
    ).reset_index()
    summary["dose"] = summary["regime"].map(_dose)
    summary = summary.dropna(subset=["dose"]).sort_values("dose").copy()
    summary["pct_kicked"] = summary["kicked"] / summary["n"]
    summary["pct_destcoh"] = summary["destcoh"] / summary["n"]
    summary["pct_srcesc"] = summary["srcesc"] / summary["n"]
    ci = summary.apply(
        lambda r: _wilson(r["pct_destcoh"], r["n"]), axis=1, result_type="expand"
    )
    summary["destcoh_lo"] = ci[0]
    summary["destcoh_hi"] = ci[1]

    # transition-entropy diagnostic: H(C_T | C_+ kicked) per dose
    df_p_kicked = df_p[df_p["kicked"] == 1].copy()
    ent_rows = []
    for dose, grp in df_p_kicked.groupby(df_p_kicked["regime"].map(_dose)):
        if dose is None:
            continue
        # H(C_T | C_+) = sum_{c+} P(c+) H(C_T | c+)
        joint = grp.groupby(["post_cluster", "end_cluster"]).size().unstack(fill_value=0)
        if joint.empty:
            continue
        row_totals = joint.sum(axis=1)
        cond_p = joint.div(row_totals, axis=0).fillna(0)
        with np.errstate(divide="ignore", invalid="ignore"):
            row_ent = -(cond_p * np.where(cond_p > 0, np.log2(cond_p), 0)).sum(axis=1)
        weights = row_totals / row_totals.sum()
        H = float((row_ent * weights).sum())
        ent_rows.append({"dose": int(dose), "H_T_given_plus_kicked": H})
    ent_df = pd.DataFrame(ent_rows)
    summary = summary.merge(ent_df, on="dose", how="left")
    return summary


def _dip_magnitude(summary: pd.DataFrame, col: str = "pct_destcoh") -> float:
    """Delta = S(2000) - mean(S(1500), S(3000)). Negative = dip."""
    g = summary.set_index("dose")[col]
    if not all(d in g.index for d in (1500, 2000, 3000)):
        return float("nan")
    return float(g[2000] - 0.5 * (g[1500] + g[3000]))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []

    print("=" * 70)
    print("Experiment A: dip-mechanism sweep")
    print("=" * 70)
    print(f"Variants: 3 observables x {len(K_GRID)} k-values x 4 plus_step values")
    print()

    for obs in OBSERVABLES:
        for k in K_GRID:
            for plus_step in (15, 16, 17, 18):
                if plus_step == 15:
                    label = "canonical_t15"
                else:
                    label = f"delayed_t{plus_step}"
                summary = _persistence_table(obs, k, plus_step=plus_step)
                dip_dst = _dip_magnitude(summary, "pct_destcoh")
                dip_src = _dip_magnitude(summary, "pct_srcesc")
                # sample point estimates for context
                pts = summary.set_index("dose")["pct_destcoh"].to_dict()
                kpts = summary.set_index("dose")["pct_kicked"].to_dict()
                rows.append({
                    "observable": obs,
                    "k": k,
                    "plus_step": plus_step,
                    "label": label,
                    "S_1500": pts.get(1500, float("nan")),
                    "S_2000": pts.get(2000, float("nan")),
                    "S_3000": pts.get(3000, float("nan")),
                    "K_2000": kpts.get(2000, float("nan")),
                    "dip_destcoh": dip_dst,
                    "dip_srcesc": dip_src,
                })
                print(f"  {obs:14s} k={k:>2d} plus={plus_step}  S(1500/2000/3000)="
                      f"{pts.get(1500, np.nan):.3f}/{pts.get(2000, np.nan):.3f}/"
                      f"{pts.get(3000, np.nan):.3f}  dip={dip_dst:+.3f}")

        # Time-integrated variant V3 (only for k=12, t+=15 - the canonical setup)
        summary_ti = _persistence_table(
            obs, 12, plus_step=15, time_integrated_window=LATE_WINDOW
        )
        pts_ti = summary_ti.set_index("dose")["pct_destcoh"].to_dict()
        rows.append({
            "observable": obs,
            "k": 12,
            "plus_step": 15,
            "label": f"time_integrated_25_29",
            "S_1500": pts_ti.get(1500, float("nan")),
            "S_2000": pts_ti.get(2000, float("nan")),
            "S_3000": pts_ti.get(3000, float("nan")),
            "K_2000": float("nan"),
            "dip_destcoh": _dip_magnitude(summary_ti, "pct_destcoh"),
            "dip_srcesc": _dip_magnitude(summary_ti, "pct_srcesc"),
        })
        print(f"  {obs:14s}  TIME-INTEGRATED 25..29   "
              f"S(1500/2000/3000)={pts_ti.get(1500, np.nan):.3f}/"
              f"{pts_ti.get(2000, np.nan):.3f}/{pts_ti.get(3000, np.nan):.3f}  "
              f"dip={_dip_magnitude(summary_ti):+.3f}")
        print()

    df = pd.DataFrame(rows)
    csv_path = OUT_DIR / "table.csv"
    df.to_csv(csv_path, index=False)
    print(f"\nwrote {csv_path}")

    # Summary verdict
    print("\n" + "=" * 70)
    print("VERDICT: under what variants does the dip vanish (|dip| < 0.05)?")
    print("=" * 70)
    canonical = df[(df["observable"] == "context_tail") & (df["k"] == 12) &
                   (df["plus_step"] == 15) & (df["label"] == "canonical_t15")]
    if not canonical.empty:
        canon_dip = float(canonical["dip_destcoh"].iloc[0])
        print(f"Canonical (context_tail, k=12, t+=15): dip = {canon_dip:+.3f}")
    survived = df[df["dip_destcoh"] < -0.05].copy()
    vanished = df[df["dip_destcoh"].between(-0.05, 0.05)].copy()
    print(f"\nDip vanishes (|dip| < 0.05) in {len(vanished)} / {len(df)} setups.")
    print(f"Dip survives (dip < -0.05) in {len(survived)} / {len(df)} setups.")
    if not vanished.empty:
        print("\nVariants where dip VANISHES:")
        for _, r in vanished.iterrows():
            print(f"  {r['observable']:14s} k={r['k']:>2d} {r['label']:25s}  "
                  f"dip={r['dip_destcoh']:+.3f}")
    print()
    print("Top survivors (sharpest dip):")
    for _, r in survived.nsmallest(5, "dip_destcoh").iterrows():
        print(f"  {r['observable']:14s} k={r['k']:>2d} {r['label']:25s}  "
              f"dip={r['dip_destcoh']:+.3f}")


if __name__ == "__main__":
    main()
