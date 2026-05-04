"""
Build RESULTS_nano.md — cell-by-cell cross-model comparison of the
gpt-4o-mini baseline vs the gpt-4.1-nano replication.

For each pair (`exp_X` + `exp_X_gpt4nano`) we extract:
  - H1a / H1b two-axis verdict   (from reports/report.md)
  - Mean recurrence rate         (metrics/recurrence.csv, regime=recursive)
  - Mean basin score             (metrics/basin.csv, regime=recursive)
  - Sharpness dim (late)         (metrics/dynamics.csv, when present)
  - Basin predictability acc(10) (reports/basin_predictability/...summary.json)

Then summarize: how many cells reproduce each headline diagnostic to
within ε of the gpt-4o-mini baseline.

Usage:
    python -m scripts.compare_cross_model
    python -m scripts.compare_cross_model --suffix gpt4nano

Output: RESULTS_nano.md at the repo root, plus a summary printed to
stdout.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"


def _verdicts(report_md: Path) -> tuple[str, str]:
    """Return (H1a, H1b) verdict labels from a report.md."""
    if not report_md.exists():
        return ("?", "?")
    txt = report_md.read_text(encoding="utf-8")
    h1a = re.search(r"H1a convergence:\s*`([^`]+)`", txt)
    h1b = re.search(r"H1b recurrence:\s*`([^`]+)`", txt)
    return (h1a.group(1) if h1a else "?", h1b.group(1) if h1b else "?")


def _mean_recurrence(metrics_csv: Path, regime: str = "recursive") -> float | None:
    """Mean recurrence rate across the recursive regime, all observables / spaces."""
    if not metrics_csv.exists():
        return None
    try:
        df = pd.read_csv(metrics_csv)
    except Exception:
        return None
    if "regime" not in df.columns or "recurrence_rate" not in df.columns:
        return None
    sub = df[df["regime"] == regime]
    if sub.empty:
        return None
    return float(sub["recurrence_rate"].mean())


def _mean_basin(metrics_csv: Path, regime: str = "recursive") -> float | None:
    """basin.csv has no `regime` column — it's already implicit (the
    per-target-cluster basin score per observable / space / family / ic).
    Take the mean across all rows."""
    if not metrics_csv.exists():
        return None
    try:
        df = pd.read_csv(metrics_csv)
    except Exception:
        return None
    if "basin_score" not in df.columns:
        return None
    return float(df["basin_score"].mean())


def _sharpness_dim_late(dynamics_csv: Path) -> float | None:
    if not dynamics_csv.exists():
        return None
    try:
        df = pd.read_csv(dynamics_csv)
    except Exception:
        return None
    # Look for sharpness_dim at the late window (window == "late" or step >= T/2)
    if "sharpness_dim" in df.columns:
        if "window" in df.columns and "late" in df["window"].astype(str).values:
            sub = df[df["window"].astype(str) == "late"]
        else:
            sub = df.tail(max(1, len(df) // 2))
        v = sub["sharpness_dim"].dropna()
        return float(v.mean()) if len(v) else None
    return None


def _basin_pred_acc_k10(summary_json: Path) -> float | None:
    """basin_predictability_summary.json shape:
        {"rows": [{"regime": "recursive", "step": 10, "top1": 0.83, ...}, ...]}
    We pick the recursive-regime row at step=10 (the canonical reporting
    point in the paper), or the closest available step ≤ 10."""
    if not summary_json.exists():
        return None
    try:
        d = json.loads(summary_json.read_text(encoding="utf-8"))
    except Exception:
        return None
    rows = d.get("rows") or []
    candidates = [r for r in rows
                  if isinstance(r, dict)
                  and r.get("regime") == "recursive"
                  and "top1" in r
                  and isinstance(r.get("step"), (int, float))]
    if not candidates:
        return None
    # Prefer step=10 exactly, else the nearest step ≤ 10 (or smallest > 10)
    by_step = {int(r["step"]): float(r["top1"]) for r in candidates}
    if 10 in by_step:
        return by_step[10]
    le10 = sorted(s for s in by_step if s <= 10)
    if le10:
        return by_step[le10[-1]]
    gt10 = sorted(s for s in by_step if s > 10)
    return by_step[gt10[0]] if gt10 else None


def _extract(exp_dir: Path) -> dict:
    return {
        "verdicts": _verdicts(exp_dir / "reports" / "report.md"),
        "recurrence": _mean_recurrence(exp_dir / "metrics" / "recurrence.csv"),
        "basin": _mean_basin(exp_dir / "metrics" / "basin.csv"),
        "sharpness": _sharpness_dim_late(exp_dir / "metrics" / "dynamics.csv"),
        "basin_pred_k10": _basin_pred_acc_k10(
            exp_dir / "reports" / "basin_predictability" / "basin_predictability_summary.json"
        ),
    }


def _fmt(v) -> str:
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:.3f}"
    return str(v)


def _diff(a, b) -> str:
    if a is None or b is None:
        return "—"
    return f"{b - a:+.3f}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suffix", default="gpt4nano",
                    help="cross-model suffix to compare against baseline")
    ap.add_argument("--out", default=str(REPO / "RESULTS_nano.md"))
    args = ap.parse_args()

    suf = "_" + args.suffix.lstrip("_")
    base_dirs = sorted(p for p in DATA.iterdir()
                       if p.is_dir() and p.name.startswith("exp_")
                       and not p.name.endswith(suf))
    rows: list[dict] = []
    for base in base_dirs:
        nano = DATA / (base.name + suf)
        if not nano.is_dir():
            continue
        b = _extract(base)
        n = _extract(nano)
        rows.append({
            "experiment_id": base.name,
            "h1a_base": b["verdicts"][0], "h1a_nano": n["verdicts"][0],
            "h1b_base": b["verdicts"][1], "h1b_nano": n["verdicts"][1],
            "recurrence_base": b["recurrence"], "recurrence_nano": n["recurrence"],
            "basin_base": b["basin"], "basin_nano": n["basin"],
            "sharpness_base": b["sharpness"], "sharpness_nano": n["sharpness"],
            "bp_k10_base": b["basin_pred_k10"], "bp_k10_nano": n["basin_pred_k10"],
        })

    if not rows:
        print(f"no paired cells found for suffix '{suf}'")
        return 1

    # Build markdown
    n_total = len(rows)
    h1a_match = sum(1 for r in rows if r["h1a_base"] == r["h1a_nano"])
    h1b_match = sum(1 for r in rows if r["h1b_base"] == r["h1b_nano"])
    both_match = sum(1 for r in rows if r["h1a_base"] == r["h1a_nano"] and r["h1b_base"] == r["h1b_nano"])

    def _within(key: str, eps: float) -> int:
        c = 0
        for r in rows:
            a, b = r[f"{key}_base"], r[f"{key}_nano"]
            if a is not None and b is not None and abs(a - b) <= eps:
                c += 1
        return c

    def _both_present(key: str) -> int:
        return sum(1 for r in rows
                   if r[f"{key}_base"] is not None and r[f"{key}_nano"] is not None)

    rec_within_005 = _within("recurrence", 0.05)
    rec_total = _both_present("recurrence")
    bas_within_005 = _within("basin", 0.05)
    bas_total = _both_present("basin")
    bp_within_010 = _within("bp_k10", 0.10)
    bp_total = _both_present("bp_k10")

    md = []
    md.append(f"# RESULTS_nano — cross-model replication audit (gpt-4o-mini → gpt-4.1-nano)\n")
    md.append(
        "Generated by `scripts/compare_cross_model.py`. Reads each paired "
        "`exp_X` + `exp_X_gpt4nano` cell's metrics + report files and "
        "tabulates the gpt-4o-mini baseline value alongside the nano "
        "replication value. The summary counts how many cells reproduce "
        "each headline diagnostic to within tight tolerance.\n"
    )
    md.append("## Summary\n")
    md.append(f"- Paired cells audited: **{n_total}**\n")
    md.append(f"- H1a verdict matches: **{h1a_match} / {n_total}**\n")
    md.append(f"- H1b verdict matches: **{h1b_match} / {n_total}**\n")
    md.append(f"- Both H1a + H1b match: **{both_match} / {n_total}**\n")
    md.append(f"- Recurrence rate within ±0.05: **{rec_within_005} / {rec_total}** cells with both values\n")
    md.append(f"- Basin score within ±0.05: **{bas_within_005} / {bas_total}** cells with both values\n")
    md.append(f"- Basin pred acc(k=10) within ±0.10: **{bp_within_010} / {bp_total}** cells with both values\n")
    md.append("")

    md.append("## Per-cell comparison\n")
    md.append(
        "| experiment_id | H1a base→nano | H1b base→nano | recurrence (base / nano / Δ) "
        "| basin (base / nano / Δ) | sharpness late (base / nano / Δ) "
        "| bp acc(k=10) (base / nano / Δ) |\n"
    )
    md.append(
        "|---|---|---|---|---|---|---|\n"
    )
    for r in rows:
        md.append(
            "| `{eid}` | {h1a_b}→{h1a_n} | {h1b_b}→{h1b_n} "
            "| {rb} / {rn} / {rd} | {bb} / {bn} / {bd} "
            "| {sb} / {sn} / {sd} | {pb} / {pn} / {pd} |\n".format(
                eid=r["experiment_id"],
                h1a_b=r["h1a_base"], h1a_n=r["h1a_nano"],
                h1b_b=r["h1b_base"], h1b_n=r["h1b_nano"],
                rb=_fmt(r["recurrence_base"]), rn=_fmt(r["recurrence_nano"]),
                rd=_diff(r["recurrence_base"], r["recurrence_nano"]),
                bb=_fmt(r["basin_base"]), bn=_fmt(r["basin_nano"]),
                bd=_diff(r["basin_base"], r["basin_nano"]),
                sb=_fmt(r["sharpness_base"]), sn=_fmt(r["sharpness_nano"]),
                sd=_diff(r["sharpness_base"], r["sharpness_nano"]),
                pb=_fmt(r["bp_k10_base"]), pn=_fmt(r["bp_k10_nano"]),
                pd=_diff(r["bp_k10_base"], r["bp_k10_nano"]),
            )
        )
    md.append("")
    md.append("Notes:\n")
    md.append("- Recurrence + basin values are means across the recursive regime, all observables × all PCA / t-SNE projection spaces.\n")
    md.append("- Perturbation experiments do not have a `recursive` regime baseline (regime encodes the perturbation condition); their recurrence / basin cells will read `—`. The H1a/H1b verdicts in those cells are reporting artifacts and not directly comparable.\n")
    md.append("- Sharpness dim is from `metrics/dynamics.csv` when present (requires runs_per_condition ≥ 2). Smaller exploratory cells (e.g. D2 at exploratory scale) do not produce this column.\n")

    out = Path(args.out)
    out.write_text("".join(md), encoding="utf-8")

    # Console summary
    print(f"wrote {out} ({len(rows)} paired cells)")
    print(f"H1a match: {h1a_match}/{n_total}    H1b match: {h1b_match}/{n_total}    both: {both_match}/{n_total}")
    print(f"recurrence ±0.05: {rec_within_005}/{rec_total}")
    print(f"basin      ±0.05: {bas_within_005}/{bas_total}")
    print(f"bp acc(10) ±0.10: {bp_within_010}/{bp_total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
