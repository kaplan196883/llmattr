"""
Run the paper's main theses as machine-checkable pass/fail tests on
both gpt-4o-mini (baseline) and gpt-4.1-nano (replication).

For each thesis we read the canonical metrics file from `data/exp_*/`
and `data/exp_*_<suffix>/`, evaluate the threshold predicate, and
emit a status row. The script writes THESES_nano.md (or whatever
--out specifies) with a per-thesis pass/fail summary.

Theses verified:
  T1. Recurrence-rate regime ordering: O2 / O3 stay high (>0.7),
      O1 / D1 stay low (<0.4) at publication scale.
  T2. Replace-mode capitulation under perturbation: O2 + O3 pilots
      show switching rate > 0.85 under all three perturbed conditions
      (neutral / lorem / adversarial).
  T3. O1 contractive resistance to out-of-distribution: O1 pilot
      control ≤ 0.05, and O1 pilot neutral + lorem in [0.10, 0.40]
      (the 24% drift-floor band).
  T4. O1 in-distribution adversarial > drift floor: O1 pilot
      adversarial switching strictly greater than O1 pilot lorem.
  T5. D1 stylistic-basin behavior under perturbation: D1 pilot
      switching > 0.30 under neutral (basins are stylistic, easily
      flipped by light prompting).
  T6. Publication-scale headline verdicts: O1 continue / O2
      paraphrase-replace / O3 summarize-negate-replace / D1 dialog v2
      preserve their two-axis H1a/H1b labels.

Usage:
    python -m scripts.check_theses_cross_model
    python -m scripts.check_theses_cross_model --suffix gpt4nano

Output: THESES_nano.md (default), plus a console summary.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def _switching(exp_dir: Path) -> dict[str, float] | None:
    """Read perturbation switching_summary.csv → {cond: switch_rate}."""
    p = exp_dir / "reports" / "perturbation" / "switching_summary.csv"
    if not p.exists():
        return None
    try:
        df = pd.read_csv(p)
    except Exception:
        return None
    if "condition" not in df.columns or "switch_rate" not in df.columns:
        return None
    return {str(r["condition"]): float(r["switch_rate"])
            for _, r in df.iterrows()}


def _mean_recurrence(exp_dir: Path) -> float | None:
    p = exp_dir / "metrics" / "recurrence.csv"
    if not p.exists():
        return None
    try:
        df = pd.read_csv(p)
    except Exception:
        return None
    if "regime" not in df.columns or "recurrence_rate" not in df.columns:
        return None
    sub = df[df["regime"] == "recursive"]
    if sub.empty:
        return None
    return float(sub["recurrence_rate"].mean())


def _verdicts(exp_dir: Path) -> tuple[str, str]:
    p = exp_dir / "reports" / "report.md"
    if not p.exists():
        return ("?", "?")
    txt = p.read_text(encoding="utf-8")
    h1a = re.search(r"H1a convergence:\s*`([^`]+)`", txt)
    h1b = re.search(r"H1b recurrence:\s*`([^`]+)`", txt)
    return (h1a.group(1) if h1a else "?", h1b.group(1) if h1b else "?")


# ---------------------------------------------------------------------------
# Thesis tests
# ---------------------------------------------------------------------------

class Result:
    __slots__ = ("ok", "value", "detail")
    def __init__(self, ok: bool | None, value: object, detail: str) -> None:
        self.ok, self.value, self.detail = ok, value, detail

    @property
    def status(self) -> str:
        if self.ok is None: return "n/a"
        return "PASS" if self.ok else "FAIL"


def _t1_recurrence_ordering(suf: str) -> Result:
    """O2/O3 > 0.7, O1/D1 < 0.4 on the four pub-scale headlines."""
    cells = {
        "O1": "exp_pub_O1_continue",
        "O2": "exp_pub_O2_paraphrase_replace",
        "O3": "exp_pub_O3_summarize_negate_replace",
        "D1": "exp_pub_D1_dialog_curious_helpful_v2",
    }
    vals: dict[str, float | None] = {}
    for k, eid in cells.items():
        vals[k] = _mean_recurrence(DATA / (eid + suf))
    if any(v is None for v in vals.values()):
        return Result(None, vals, "missing recurrence.csv for one or more pub-scale cells")
    high_ok = vals["O2"] > 0.70 and vals["O3"] > 0.70
    low_ok = vals["O1"] < 0.40 and vals["D1"] < 0.40
    sep_ok = min(vals["O2"], vals["O3"]) > max(vals["O1"], vals["D1"])
    ok = high_ok and low_ok and sep_ok
    detail = (f"O1={vals['O1']:.3f} O2={vals['O2']:.3f} "
              f"O3={vals['O3']:.3f} D1={vals['D1']:.3f}; "
              f"high>0.70: {high_ok}; low<0.40: {low_ok}; "
              f"min(O2,O3)>max(O1,D1): {sep_ok}")
    return Result(ok, vals, detail)


def _t2_replace_capitulation(suf: str) -> Result:
    """O2 + O3 pilots: switching > 0.85 under neutral / lorem / adversarial."""
    o2 = _switching(DATA / ("exp_perturb_O2_pilot" + suf))
    o3 = _switching(DATA / ("exp_perturb_O3_pilot" + suf))
    if o2 is None or o3 is None:
        return Result(None, {"O2": o2, "O3": o3},
                      "missing switching_summary.csv for O2 or O3 pilot")
    perts = ("neutral", "lorem", "adversarial")
    failures = []
    for tag, d in (("O2", o2), ("O3", o3)):
        for p in perts:
            v = d.get(p)
            if v is None or v < 0.85:
                failures.append(f"{tag}/{p}={v}")
    ok = not failures
    detail = (f"O2 {o2}; O3 {o3}; "
              + ("all > 0.85" if ok else f"failures: {failures}"))
    return Result(ok, {"O2": o2, "O3": o3}, detail)


def _t3_o1_drift_floor(suf: str) -> Result:
    """O1 pilot: control ≤ 0.05; neutral + lorem in [0.10, 0.40]."""
    o1 = _switching(DATA / ("exp_perturb_O1_pilot" + suf))
    if o1 is None:
        return Result(None, None, "missing switching_summary.csv for O1 pilot")
    ctrl = o1.get("control")
    neu = o1.get("neutral")
    lor = o1.get("lorem")
    if any(v is None for v in (ctrl, neu, lor)):
        return Result(None, o1, "missing one of control/neutral/lorem in O1 pilot")
    ok_ctrl = ctrl <= 0.05
    ok_neu = 0.10 <= neu <= 0.40
    ok_lor = 0.10 <= lor <= 0.40
    ok = ok_ctrl and ok_neu and ok_lor
    detail = (f"control={ctrl:.3f} neutral={neu:.3f} lorem={lor:.3f}; "
              f"control≤0.05: {ok_ctrl}; neutral∈[0.10,0.40]: {ok_neu}; "
              f"lorem∈[0.10,0.40]: {ok_lor}")
    return Result(ok, o1, detail)


def _t4_o1_adversarial_above_floor(suf: str) -> Result:
    """O1 pilot: adversarial > lorem (in-distribution beats OOD)."""
    o1 = _switching(DATA / ("exp_perturb_O1_pilot" + suf))
    if o1 is None:
        return Result(None, None, "missing switching_summary.csv for O1 pilot")
    adv, lor = o1.get("adversarial"), o1.get("lorem")
    if adv is None or lor is None:
        return Result(None, o1, "missing adversarial or lorem in O1 pilot")
    ok = adv > lor
    detail = (f"adversarial={adv:.3f} > lorem={lor:.3f}? {ok}; "
              f"margin={adv - lor:+.3f}")
    return Result(ok, {"adversarial": adv, "lorem": lor}, detail)


def _t5_d1_stylistic_response(suf: str) -> Result:
    """D1 pilot: switching > 0.30 under neutral (multi-basin susceptible)."""
    d1 = _switching(DATA / ("exp_perturb_D1_pilot" + suf))
    if d1 is None:
        return Result(None, None, "missing switching_summary.csv for D1 pilot")
    neu = d1.get("neutral")
    if neu is None:
        return Result(None, d1, "missing neutral condition")
    ok = neu > 0.30
    detail = f"neutral={neu:.3f} > 0.30? {ok}"
    return Result(ok, {"neutral": neu}, detail)


def _t6_pub_verdicts(suf: str) -> Result:
    """Pub-scale headline cells preserve canonical H1a/H1b verdicts."""
    expected = {
        "exp_pub_O1_continue":               ("strong_support", "weak_support"),
        "exp_pub_O2_paraphrase_replace":     ("strong_support", "not_supported"),
        "exp_pub_O3_summarize_negate_replace":("strong_support","not_supported"),
        "exp_pub_D1_dialog_curious_helpful_v2":("strong_support","weak_support"),
    }
    actual: dict[str, tuple[str, str]] = {}
    for eid in expected:
        actual[eid] = _verdicts(DATA / (eid + suf))
    misses = [eid for eid, exp in expected.items() if actual[eid] != exp]
    ok = not misses
    detail = ("; ".join(f"{eid}: {actual[eid]} (expected {exp})"
                        for eid, exp in expected.items()))
    return Result(ok, actual, detail)


THESES = [
    ("T1",
     "Recurrence-rate regime ordering",
     "O2/O3 > 0.70 and O1/D1 < 0.40 at pub scale; min(O2,O3) > max(O1,D1).",
     _t1_recurrence_ordering),
    ("T2",
     "Replace-mode capitulation under perturbation",
     "O2 and O3 pilot switching > 0.85 for all three perturbed conditions.",
     _t2_replace_capitulation),
    ("T3",
     "O1 contractive: out-of-distribution drift-floor band",
     "O1 pilot control ≤ 0.05; neutral ∈ [0.10, 0.40]; lorem ∈ [0.10, 0.40].",
     _t3_o1_drift_floor),
    ("T4",
     "O1 contractive: adversarial > out-of-distribution",
     "O1 pilot adversarial switching > O1 pilot lorem switching.",
     _t4_o1_adversarial_above_floor),
    ("T5",
     "D1 stylistic-multi-basin susceptibility",
     "D1 pilot neutral switching > 0.30 (basin-flip under light prompting).",
     _t5_d1_stylistic_response),
    ("T6",
     "Publication-scale verdict labels",
     "O1 continue, O2 paraphrase-replace, O3 summarize-negate-replace, "
     "D1 dialog v2 all carry expected (H1a, H1b) tuples.",
     _t6_pub_verdicts),
]


def _emoji(status: str) -> str:
    return {"PASS": "✅", "FAIL": "❌", "n/a": "⚪"}.get(status, "?")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suffix", default="gpt4nano",
                    help="cross-model suffix to compare against the "
                         "(unsuffixed) gpt-4o-mini baseline")
    ap.add_argument("--out", default=str(REPO / "THESES_nano.md"))
    args = ap.parse_args()

    suf = "_" + args.suffix.lstrip("_")

    md = ["# THESES_nano — paper-thesis verification across two LLMs\n\n",
          "Generated by `scripts/check_theses_cross_model.py`. "
          "Each thesis is encoded as a machine-checkable predicate "
          "over canonical metric files (`switching_summary.csv`, "
          "`recurrence.csv`, `report.md`). "
          "We evaluate it on the gpt-4o-mini baseline and on the "
          f"`{args.suffix}` replication, then report PASS / FAIL / "
          "n/a (data missing).\n\n"]

    md.append("## Summary\n\n")
    md.append("| ID | Thesis | gpt-4o-mini | gpt-4.1-nano |\n")
    md.append("|---|---|---|---|\n")

    rows_summary = []
    n_pass_base = n_pass_nano = 0
    n_total = 0
    for tid, title, predicate, fn in THESES:
        rb = fn("")
        rn = fn(suf)
        rows_summary.append((tid, title, predicate, rb, rn))
        n_total += 1
        if rb.ok is True: n_pass_base += 1
        if rn.ok is True: n_pass_nano += 1
        md.append(f"| **{tid}** | {title} | {_emoji(rb.status)} {rb.status} "
                  f"| {_emoji(rn.status)} {rn.status} |\n")

    md.append(f"\n**Score: gpt-4o-mini {n_pass_base} / {n_total}, "
              f"gpt-4.1-nano {n_pass_nano} / {n_total}.**\n\n")

    md.append("## Per-thesis details\n\n")
    for tid, title, predicate, rb, rn in rows_summary:
        md.append(f"### {tid}. {title}\n\n")
        md.append(f"**Predicate:** {predicate}\n\n")
        md.append(f"- gpt-4o-mini: {_emoji(rb.status)} **{rb.status}** — {rb.detail}\n")
        md.append(f"- gpt-4.1-nano: {_emoji(rn.status)} **{rn.status}** — {rn.detail}\n\n")

    out = Path(args.out)
    out.write_text("".join(md), encoding="utf-8")
    print(f"wrote {out}")
    print(f"gpt-4o-mini: {n_pass_base} / {n_total}    gpt-4.1-nano: {n_pass_nano} / {n_total}")
    for tid, title, _pred, rb, rn in rows_summary:
        print(f"  {tid}  base={rb.status:4s}  nano={rn.status:4s}  {title}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
