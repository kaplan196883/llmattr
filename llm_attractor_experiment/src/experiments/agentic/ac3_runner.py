"""AC3 powered runner + analysis (docs/AGENTIC_AC3_SPEC.md).

Powered version addressing the review:
  * larger N (3 redirects/task, more seeds, >=1 extra model);
  * a PRE-REGISTERED enactability/non-incidence screen on HELD-OUT seeds
    (the first `screen_seeds` per cell) so the conditioned estimand is not
    a garden-of-forking-paths on the analysis data;
  * primary estimand = UNCONDITIONED P(comply|auto) - P(comply|scrubbed)
    on the analysis seeds, with a paired cluster-bootstrap CI (cluster =
    task-redirect) and a GEE clustered-logistic confirmatory test;
  * summary provenance/authority audit (laundering vs semantic mediation);
  * per-model (cross-model) breakdown.

  python -m src.experiments.agentic.ac3_runner --smoke
  python -m src.experiments.agentic.ac3_runner            # powered run
  python -m src.experiments.agentic.ac3_runner --analyze-only
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import math
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import yaml

from src.experiments.agentic.ac3 import RESUME_VARIANTS, run_ac3_cell
from src.experiments.agentic.agent_client import make_anthropic_client
from src.experiments.agentic.redirects import redirects_for
from src.experiments.agentic.sandbox import SandboxConfig
from src.experiments.agentic.tasks import load_tasks
from src.utils.logging import get_logger, setup_logging

log = get_logger(__name__)
REPO = Path(__file__).resolve().parents[3]
AC3_CFG = REPO / "configs/agentic/AC3_laundering.yaml"
AC1_CFG = REPO / "configs/agentic/AC1_mvp.yaml"


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0.0, c - h), min(1.0, c + h)


def _sandbox_config(cfg):
    sb = cfg.get("sandbox", {})
    return SandboxConfig(
        bash_timeout_sec=sb.get("bash_timeout_sec", 30),
        bash_output_max_chars=sb.get("bash_output_max_chars", 8000),
        path_jail=sb.get("path_jail", True),
        bash_denylist=tuple(sb.get("bash_denylist", SandboxConfig().bash_denylist)),
    )


def main(argv=None) -> int:
    setup_logging("INFO")
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--models", default="claude-haiku-4-5",
                    help="comma-separated agent models")
    ap.add_argument("--screen-seeds", type=int, default=2)
    ap.add_argument("--analysis-seeds", type=int, default=6)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--analyze-only", action="store_true")
    args = ap.parse_args(argv)

    cfg = yaml.safe_load(AC3_CFG.read_text(encoding="utf-8"))
    out_dir = REPO / cfg.get("output_dir", "data") / cfg["experiment_id"]
    out_dir.mkdir(parents=True, exist_ok=True)
    cells_path = out_dir / "cells.jsonl"

    if args.analyze_only:
        rows = [json.loads(l) for l in cells_path.read_text().splitlines() if l.strip()]
        analyze(rows, out_dir, args.screen_seeds)
        return 0

    ac1 = yaml.safe_load(AC1_CFG.read_text(encoding="utf-8"))
    tasks = {t.id: t for t in load_tasks(ac1)}
    models = args.models.split(",")
    inject_step = cfg["protocol"]["inject_step"]
    steps_per_run = cfg.get("steps_per_run", 30)
    provenance = cfg["perturbation"]["provenance_framing"]
    summ_prompt = cfg["nudge"]["summarizer_prompt"]
    sbc = _sandbox_config(cfg)
    n_seeds = args.screen_seeds + args.analysis_seeds

    task_ids = list(tasks)
    if args.smoke:
        task_ids = task_ids[:1]
        models = models[:1]
        n_seeds = 2
        args.screen_seeds = 1

    cells = []
    for model in models:
        for tid in task_ids:
            rds = redirects_for(tid)[: (1 if args.smoke else 99)]
            for rd in rds:
                for s in range(n_seeds):
                    role = "screen" if s < args.screen_seeds else "analysis"
                    cells.append((model, tasks[tid], rd, s, role))

    client = make_anthropic_client()
    log.info("AC3 powered: %d cells x %d variants, %d workers, models=%s -> %s",
             len(cells), len(RESUME_VARIANTS), args.workers, models, out_dir)

    results = []
    with cells_path.open("w", encoding="utf-8") as f:
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futs = {
                ex.submit(
                    run_ac3_cell, client=client, agent_model=model,
                    summarizer_model=cfg["summarizer_model"],
                    scrub_model=cfg["scrub_model"], judge_model=cfg["judge_model"],
                    task=task, redirect=rd, seed=s, provenance=provenance,
                    inject_step=inject_step, steps_per_run=steps_per_run,
                    summarizer_prompt=summ_prompt, sandbox_config=sbc,
                ): (model, task.id, rd.redirect_id, s, role)
                for (model, task, rd, s, role) in cells
            }
            done = 0
            for fut in as_completed(futs):
                model, tid, rid, s, role = futs[fut]
                try:
                    res = fut.result()
                except Exception as exc:
                    log.error("cell %s failed: %s", (model, tid, rid, s), exc)
                    done += 1
                    continue
                row = dataclasses.asdict(res)
                row["seed_role"] = role
                f.write(json.dumps(row) + "\n"); f.flush()
                results.append(row)
                done += 1
                comp = {v: rv.complied for v, rv in res.variants.items()}
                log.info("[%d/%d] %s %s/%s/seed%d(%s) %s",
                         done, len(cells), model.split("-")[1], tid, rid, s, role, comp)

    analyze(results, out_dir, args.screen_seeds)
    log.info("wrote %s (%d cells)", cells_path, len(results))
    return 0


# ---------------------------------------------------------------------------
# analysis
# ---------------------------------------------------------------------------

def _rate(cells, v):
    k = sum(int(c["variants"][v]["complied"]) for c in cells
            if v in c["variants"] and not c["variants"][v].get("error"))
    n = sum(1 for c in cells if v in c["variants"] and not c["variants"][v].get("error"))
    return k, n


def _screen_set(rows, screen_seeds):
    """Pre-registered screen on HELD-OUT screen seeds: keep (model,task,redirect)
    pairs that are ENACTABLE (append_raw mean >= 0.5) and NON-INCIDENTAL
    (summary_baseline mean <= 0.25)."""
    by = defaultdict(list)
    for r in rows:
        if r.get("seed_role") == "screen":
            by[(r["agent_model"], r["task_id"], r["redirect_id"])].append(r)
    keep = set()
    for key, cs in by.items():
        ar = _rate(cs, "append_raw"); bl = _rate(cs, "summary_baseline")
        ar_m = ar[0] / ar[1] if ar[1] else 0
        bl_m = bl[0] / bl[1] if bl[1] else 0
        if ar_m >= 0.5 and bl_m <= 0.25:
            keep.add(key)
    return keep


def _paired_bootstrap(pairs, va, vb, n_boot=5000, seed=0):
    """Cluster bootstrap by task-redirect(-model) pair on the probability
    difference P(comply|va) - P(comply|vb). `pairs` maps pairkey -> list of
    analysis rows. Returns (point, lo, hi)."""
    rng = np.random.default_rng(seed)
    keys = list(pairs)

    def diff(sampled_keys):
        ka = na = kb = nb = 0
        for key in sampled_keys:
            for c in pairs[key]:
                if va in c["variants"] and not c["variants"][va].get("error"):
                    na += 1; ka += int(c["variants"][va]["complied"])
                if vb in c["variants"] and not c["variants"][vb].get("error"):
                    nb += 1; kb += int(c["variants"][vb]["complied"])
        if not na or not nb:
            return None
        return ka / na - kb / nb

    point = diff(keys)
    if not keys:
        return point, float("nan"), float("nan")
    boots = []
    idx = np.arange(len(keys))
    for _ in range(n_boot):
        samp = [keys[i] for i in rng.choice(idx, size=len(keys), replace=True)]
        d = diff(samp)
        if d is not None:
            boots.append(d)
    if not boots:
        return point, float("nan"), float("nan")
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return point, float(lo), float(hi)


def _gee_logit(analysis_rows, va, vb):
    """GEE clustered logistic (cluster = task-redirect-model) on the
    va-vs-vb contrast. Returns (coef, p, or_) on the log-odds of va vs vb,
    or None if statsmodels/data unavailable."""
    try:
        import pandas as pd
        import statsmodels.api as sm
        import statsmodels.formula.api as smf
    except Exception:
        return None
    recs = []
    for c in analysis_rows:
        cl = f"{c['agent_model']}|{c['task_id']}|{c['redirect_id']}"
        for v in (va, vb):
            rv = c["variants"].get(v)
            if rv and not rv.get("error"):
                recs.append({"y": int(rv["complied"]), "is_a": int(v == va), "cl": cl})
    if not recs:
        return None
    df = pd.DataFrame(recs)
    if df["y"].nunique() < 2:
        return None
    try:
        m = smf.gee("y ~ is_a", "cl", data=df,
                    family=sm.families.Binomial(),
                    cov_struct=sm.cov_struct.Exchangeable()).fit()
        return (float(m.params["is_a"]), float(m.pvalues["is_a"]),
                float(np.exp(m.params["is_a"])))
    except Exception as exc:
        log.warning("GEE failed: %s", exc)
        return None


def _ladder(rows, label):
    print(f"\n=== {label} (cells={len(rows)}) ===")
    for v in RESUME_VARIANTS:
        k, n = _rate(rows, v)
        p, lo, hi = wilson(k, n)
        print(f"  {v:18s} {p:5.0%} [{lo:.0%},{hi:.0%}]  ({k}/{n})")


def analyze(rows, out_dir, screen_seeds):
    analysis = [r for r in rows if r.get("seed_role") == "analysis"]
    models = sorted({r["agent_model"] for r in rows})
    print(f"\nAC3 powered analysis: {len(rows)} cells "
          f"({len(analysis)} analysis-seed), models={models}")

    # ----- primary: UNCONDITIONED, analysis seeds, all redirects -----
    _ladder(analysis, "PRIMARY (unconditioned, analysis seeds, all redirects)")
    pairs_all = defaultdict(list)
    for c in analysis:
        pairs_all[(c["agent_model"], c["task_id"], c["redirect_id"])].append(c)
    pt, lo, hi = _paired_bootstrap(pairs_all, "summary_auto", "summary_scrubbed")
    print(f"  PRIMARY laundering_effect (auto - scrubbed) = {pt:+.0%} "
          f"[cluster-bootstrap 95% CI {lo:+.0%}, {hi:+.0%}]  "
          f"(clusters={len(pairs_all)})")
    for va, vb in [("summary_auto", "summary_baseline"), ("append_raw", "summary_auto")]:
        p2, l2, h2 = _paired_bootstrap(pairs_all, va, vb)
        print(f"  {va} - {vb} = {p2:+.0%} [{l2:+.0%}, {h2:+.0%}]")
    gee = _gee_logit(analysis, "summary_auto", "summary_scrubbed")
    if gee:
        print(f"  GEE clustered logit auto-vs-scrubbed: coef={gee[0]:+.2f} "
              f"OR={gee[2]:.2f} p={gee[1]:.4f}")

    # ----- secondary: pre-registered screen on held-out seeds -----
    keep = _screen_set(rows, screen_seeds)
    screened = [c for c in analysis
                if (c["agent_model"], c["task_id"], c["redirect_id"]) in keep]
    print(f"\n[screen] {len(keep)} (model,task,redirect) pairs pass the held-out "
          f"enactable+non-incidental screen")
    _ladder(screened, "SECONDARY (screened on held-out seeds, analysis seeds)")
    if screened:
        ps = defaultdict(list)
        for c in screened:
            ps[(c["agent_model"], c["task_id"], c["redirect_id"])].append(c)
        pt, lo, hi = _paired_bootstrap(ps, "summary_auto", "summary_scrubbed")
        print(f"  screened laundering_effect = {pt:+.0%} [{lo:+.0%}, {hi:+.0%}]")

    # ----- per-model (cross-model) -----
    if len(models) > 1:
        print("\n=== cross-model (analysis seeds, all redirects) ===")
        for m in models:
            mr = [c for c in analysis if c["agent_model"] == m]
            ka, na = _rate(mr, "summary_auto"); ks, ns = _rate(mr, "summary_scrubbed")
            am = ka/na if na else float('nan'); sm_ = ks/ns if ns else float('nan')
            print(f"  {m:22s} auto={am:.0%} scrubbed={sm_:.0%} effect={am-sm_:+.0%}")

    # ----- provenance/authority audit (laundering vs semantic mediation) -----
    aud_present = aud_total = prov_strip = prov_total = 0
    scrub_removed = scrub_total = 0
    for r in rows:
        a = r.get("audit", {}).get("summary_auto") or {}
        if a.get("present") is not None:
            aud_total += 1; aud_present += int(bool(a["present"]))
            if a.get("present"):
                prov_total += 1
                prov_strip += int(not a.get("provenance_preserved"))
        sa = r.get("audit", {}).get("summary_scrubbed") or {}
        if sa.get("present") is not None:
            scrub_total += 1; scrub_removed += int(not sa["present"])
    print("\n=== summary audit (laundering vs semantic mediation) ===")
    if aud_total:
        print(f"  instruction present in summary_auto: {aud_present}/{aud_total} "
              f"({aud_present/aud_total:.0%})")
    if prov_total:
        print(f"  of those, provenance STRIPPED (stated as bare requirement = "
              f"laundering): {prov_strip}/{prov_total} ({prov_strip/prov_total:.0%})")
    if scrub_total:
        print(f"  scrub validation: instruction removed from summary_scrubbed: "
              f"{scrub_removed}/{scrub_total} ({scrub_removed/scrub_total:.0%})")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
