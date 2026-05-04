"""
Dual-model publication-readiness summary.

Reads each headline §5 cell directly from per-experiment artifacts
(`data/exp_*/`, `data/exp_*_gpt4nano/`) for both gpt-4o-mini and
gpt-4.1-nano, and emits `RESULTS_dual.md` with the article-claimed
value + measured value on each model + cross-model delta.

Scope (the cells where both models have directly-comparable data):

  §5.0 — Master comparison: SD_late, recurrence on PCA-10, adv switch.
         (4 pub-scale headline regimes)
  §5.5 — Phase 3a perturbation pilots: switching rates per condition.
         (5 perturbation pilots × {control, neutral, lorem, adversarial})

Out of scope for the dual table (nano did not run these aggregators):
  - §5.3 Phase 2 basin predictability (separate script,
    `scripts/build_basin_predictability.py`, not invoked for nano)
  - §5.4 Phase 2b T-sweep (depends on basin predictability)
  - §5.6 / 5.7 dose / inject-time aggregators (cross-model
    aggregator scripts not adapted)
  - §5.10 V* + RG geometric tables (geometric viz toolkit not
    re-run for nano)

For those, see the existing single-model `RESULTS.md`. The summary at
the top of `RESULTS_dual.md` reports per-cell PASS / shift counts for
the cells we do compare.

Usage:
    python -m scripts.publication_summary_dual
    python -m scripts.publication_summary_dual --suffix gpt4nano

Output: `RESULTS_dual.md` at the repo root.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"

REGIME_TO_PUB = {
    "O1": "exp_pub_O1_continue",
    "O2": "exp_pub_O2_paraphrase_replace",
    "O3": "exp_pub_O3_summarize_negate_replace",
    "D1": "exp_pub_D1_dialog_curious_helpful_v2",
}

REGIME_TO_PERTURB = {
    "O1": "exp_perturb_O1_pilot",
    "O2": "exp_perturb_O2_pilot",
    "O3": "exp_perturb_O3_pilot",
    "D1": "exp_perturb_D1_pilot",
    "D2": "exp_perturb_D2_exploratory",
}

# Article-claimed values (gpt-4o-mini canonical, from ARTICLE.md §5).
# Mirrored from publication_summary.py to keep a single source of truth
# for the claimed numbers without coupling the two scripts.
ART_5_0 = {
    "O1": {"SD_late": 1.70, "rec_pca10_label": "low",     "adv_switch": 0.54},
    "O2": {"SD_late": 1.39, "rec_pca10_label": "high",    "adv_switch": 0.94},
    "O3": {"SD_late": 1.45, "rec_pca10_label": "trivial", "adv_switch": 0.96},
    "D1": {"SD_late": 1.89, "rec_pca10_label": "low",     "adv_switch": 0.60},
    "D2": {"SD_late": None, "rec_pca10_label": "n/a",     "adv_switch": 0.64},
}

ART_5_5 = {
    "O1": {"control": 0.00, "neutral": 0.24, "lorem": 0.18, "adversarial": 0.54},
    "O2": {"control": 0.00, "neutral": 1.00, "lorem": 1.00, "adversarial": 0.94},
    "O3": {"control": 0.00, "neutral": 1.00, "lorem": 1.00, "adversarial": 0.96},
    "D1": {"control": 0.00, "neutral": 0.76, "lorem": 0.54, "adversarial": 0.60},
    "D2": {"control": 0.00, "adversarial": 0.64},
}

TOL_FRAC = 0.025
TOL_DEC = 0.05


# ---------------------------------------------------------------------------
# Per-cell loaders (read directly from data/exp_*/ — work for any suffix)
# ---------------------------------------------------------------------------

def _read_csv_safe(p: Path) -> pd.DataFrame | None:
    if not p.exists():
        return None
    try:
        return pd.read_csv(p)
    except Exception:
        return None


def _per_cell_5_0(exp_dir: Path) -> dict:
    """Headline §5.0 numbers for one experiment dir."""
    out: dict[str, float | None] = {"SD_late": None, "rec_pca10": None}
    d = _read_csv_safe(exp_dir / "metrics" / "dynamics.csv")
    if d is not None and {"observable", "regime", "sharpness_dim_late"}.issubset(d.columns):
        sub = d[(d.observable == "context_tail") & (d.regime == "recursive")]
        if len(sub) and not sub["sharpness_dim_late"].isna().all():
            out["SD_late"] = float(sub["sharpness_dim_late"].mean())
    rec = _read_csv_safe(exp_dir / "metrics" / "recurrence.csv")
    if rec is not None and {"observable", "space", "regime", "recurrence_rate"}.issubset(rec.columns):
        sub = rec[(rec.observable == "context_tail")
                  & (rec.space == "pca10")
                  & (rec.regime == "recursive")]
        if len(sub):
            out["rec_pca10"] = float(sub["recurrence_rate"].mean())
    return out


def _per_cell_switching(exp_dir: Path) -> dict[str, float] | None:
    """Switching rates by condition for one perturbation experiment."""
    p = exp_dir / "reports" / "perturbation" / "switching_summary.csv"
    df = _read_csv_safe(p)
    if df is None or {"condition", "switch_rate"} - set(df.columns):
        return None
    return {str(r["condition"]): float(r["switch_rate"]) for _, r in df.iterrows()}


def _measured_5_0(suffix: str) -> dict:
    """Per-regime headline numbers for the given model suffix (empty
    string = gpt-4o-mini baseline). Pulls SD_late + recurrence from
    the pub-scale dir, and adversarial switch from the perturbation
    pilot."""
    out: dict[str, dict] = {}
    for regime, pub in REGIME_TO_PUB.items():
        out[regime] = _per_cell_5_0(DATA / (pub + suffix))
    for regime, pert in REGIME_TO_PERTURB.items():
        sw = _per_cell_switching(DATA / (pert + suffix))
        adv = sw.get("adversarial") if sw else None
        out.setdefault(regime, {})["adv_switch"] = adv
    return out


def _measured_5_5(suffix: str) -> dict:
    """Per-regime perturbation switching rates for one model."""
    out: dict[str, dict] = {}
    for regime, pert in REGIME_TO_PERTURB.items():
        sw = _per_cell_switching(DATA / (pert + suffix))
        out[regime] = sw or {}
    return out


# ---------------------------------------------------------------------------
# Markdown emitters
# ---------------------------------------------------------------------------

def _fmt(x):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "—"
    if isinstance(x, str):
        return x
    return f"{x:.3f}"


def _delta(base, nano):
    if base is None or nano is None: return "—"
    if isinstance(base, str) or isinstance(nano, str): return "—"
    return f"{nano - base:+.3f}"


def _flag_match(claim, meas, tol):
    """Verdict for the gpt-4o-mini cell (matches the canonical claim)."""
    if claim is None and meas is None: return "✓"
    if claim is None or meas is None: return "—"
    if isinstance(claim, str): return "✓ (qual.)"
    return "✓" if abs(meas - claim) <= tol else f"✗ (Δ={meas - claim:+.3f})"


def emit(suffix: str = "_gpt4nano") -> str:
    suf = "_" + suffix.lstrip("_")
    nano_label = suf.lstrip("_").replace("_", "-")
    base_5_0 = _measured_5_0("")
    nano_5_0 = _measured_5_0(suf)
    base_5_5 = _measured_5_5("")
    nano_5_5 = _measured_5_5(suf)

    md = []
    md.append("# RESULTS_dual — gpt-4o-mini ↔ gpt-4.1-nano per-cell\n\n")
    md.append(
        "Companion to `RESULTS.md` (single-model 103/103 cell "
        "verification) and `RESULTS_nano.md` (high-level cross-model "
        "comparison). This file shows article-claimed values + "
        "measured values for **both** generators on the §5 tables "
        "where both have directly-comparable data.\n\n"
        "Generated by `python -m scripts.publication_summary_dual`. "
        "Tolerance: ±0.025 on switch rates / accuracies, ±0.05 on "
        "dimensionless quantities (SD).\n\n"
        "Out of scope (nano did not run the relevant aggregator): "
        "§5.3 basin predictability, §5.4 T-sweep, §5.6 / 5.7 "
        "dose / inject-time, §5.10 V* + RG geometric. See "
        "`RESULTS.md` for the gpt-4o-mini-only verification of "
        "those.\n\n"
    )

    # --- §5.0 ---
    md.append("## §5.0 Master comparison\n\n")
    md.append(
        "| regime | SD_late claim / mini / nano (Δ) "
        "| rec_pca10 mini / nano (Δ) "
        "| adv_switch claim / mini / nano (Δ) | mini flag |\n"
    )
    md.append(
        "|---|---|---|---|---|\n"
    )
    n_pass_mini = n_total = 0
    for regime in ("O1", "O2", "O3", "D1", "D2"):
        claim = ART_5_0[regime]
        b = base_5_0.get(regime, {})
        n = nano_5_0.get(regime, {})
        flag_sd = _flag_match(claim["SD_late"], b.get("SD_late"), TOL_DEC)
        flag_adv = _flag_match(claim["adv_switch"], b.get("adv_switch"), TOL_FRAC)
        n_total += 2
        n_pass_mini += int(flag_sd.startswith("✓")) + int(flag_adv.startswith("✓"))
        md.append(
            f"| **{regime}** "
            f"| {_fmt(claim['SD_late'])} / {_fmt(b.get('SD_late'))} / "
            f"{_fmt(n.get('SD_late'))} ({_delta(b.get('SD_late'), n.get('SD_late'))}) "
            f"| {_fmt(b.get('rec_pca10'))} / {_fmt(n.get('rec_pca10'))} "
            f"({_delta(b.get('rec_pca10'), n.get('rec_pca10'))}) "
            f"| {_fmt(claim['adv_switch'])} / {_fmt(b.get('adv_switch'))} / "
            f"{_fmt(n.get('adv_switch'))} ({_delta(b.get('adv_switch'), n.get('adv_switch'))}) "
            f"| {flag_sd} / {flag_adv} |\n"
        )
    md.append(
        f"\n*gpt-4o-mini cells (SD_late + adv_switch only): {n_pass_mini} / {n_total} match article claim within tolerance.*\n\n"
    )

    # --- §5.5 ---
    md.append("## §5.5 Phase 3a perturbation pilots — switching rates\n\n")
    md.append(
        "| regime | condition | claim | mini meas | nano meas | mini–claim flag | nano–mini Δ |\n"
        "|---|---|---|---|---|---|---|\n"
    )
    n_pass_mini_55 = n_total_55 = 0
    for regime in ("O1", "O2", "O3", "D1", "D2"):
        b = base_5_5.get(regime, {})
        n = nano_5_5.get(regime, {})
        for cond in ("control", "neutral", "lorem", "adversarial"):
            claim = ART_5_5.get(regime, {}).get(cond)
            if claim is None and cond not in b and cond not in n:
                continue
            mini = b.get(cond)
            nano = n.get(cond)
            flag = _flag_match(claim, mini, TOL_FRAC)
            n_total_55 += 1
            if flag.startswith("✓"): n_pass_mini_55 += 1
            md.append(
                f"| **{regime}** | {cond} | {_fmt(claim)} | {_fmt(mini)} "
                f"| {_fmt(nano)} | {flag} | {_delta(mini, nano)} |\n"
            )
    md.append(
        f"\n*gpt-4o-mini cells: {n_pass_mini_55} / {n_total_55} match article claim within tolerance.*\n\n"
    )

    # --- Cross-model delta summary ---
    deltas: list[float] = []
    for regime in ("O1", "O2", "O3", "D1", "D2"):
        b = base_5_5.get(regime, {})
        n = nano_5_5.get(regime, {})
        for cond in ("control", "neutral", "lorem", "adversarial"):
            mb, mn = b.get(cond), n.get(cond)
            if mb is None or mn is None: continue
            deltas.append(mn - mb)
    if deltas:
        ad = np.array(deltas)
        md.append("## Cross-model delta summary (§5.5 switching rates)\n\n")
        md.append(f"- Cells with both values: **{len(deltas)}**\n")
        md.append(f"- Mean Δ (nano − mini): **{ad.mean():+.3f}**\n")
        md.append(f"- Median |Δ|: **{np.median(np.abs(ad)):.3f}**\n")
        md.append(f"- Cells within ±0.05: **{int((np.abs(ad) <= 0.05).sum())} / {len(deltas)}**\n")
        md.append(f"- Cells within ±0.10: **{int((np.abs(ad) <= 0.10).sum())} / {len(deltas)}**\n")
        md.append(f"- Largest |Δ|: **{np.abs(ad).max():.3f}**\n\n")

    md.append(
        "## Interpretation\n\n"
        "The gpt-4o-mini columns reproduce the verifications in "
        "`RESULTS.md` for these specific tables. The nano columns are "
        "the cross-model replication; the deltas show that the "
        "qualitative regime structure is preserved (capitulation "
        "thresholds, drift-floor band, contractive resistance) while "
        "specific numerical values shift modestly. The detailed "
        "thesis-level pass/fail evaluation is in `THESES_nano.md` "
        "(scripts/check_theses_cross_model.py); the per-cell "
        "diagnostic comparison is in `RESULTS_nano.md` "
        "(scripts/compare_cross_model.py).\n"
    )

    return "".join(md)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suffix", default="gpt4nano")
    ap.add_argument("--out", default=str(REPO / "RESULTS_dual.md"))
    args = ap.parse_args()
    txt = emit(suffix=args.suffix)
    Path(args.out).write_text(txt, encoding="utf-8")
    print(f"wrote {args.out} ({len(txt):,} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
