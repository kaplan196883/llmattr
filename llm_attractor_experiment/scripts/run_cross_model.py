"""
Drive the 4-phase pipeline (run → embed → analyze → report) for every
config under `configs/cross_model/<tag>/`. Resumable: each (config,
phase) success is recorded in `data/aggregated/cross_model_status.csv`,
and the runner skips phases already marked done.

Usage:
    # Smoke test: one cell per provider
    python -m scripts.run_cross_model --tag gpt4nano --only exp_pub_O1_Tsweep_T08
    python -m scripts.run_cross_model --tag m2_7     --only exp_pub_O1_Tsweep_T08

    # Full sweep (all 37 configs for one tag)
    python -m scripts.run_cross_model --tag gpt4nano

    # Resume after interruption (skips completed phases automatically)
    python -m scripts.run_cross_model --tag gpt4nano

    # Run a tier (regex match on experiment_id, e.g. just pub-scale)
    python -m scripts.run_cross_model --tag gpt4nano --regex 'exp_pub_(O1|O2|O3|D1)'

    # Dry run: show what would execute, do nothing
    python -m scripts.run_cross_model --tag m2_7 --dry-run

The runner detects each config's entry-point class (`operator-style`,
`dialog`, `perturbation`) by looking for the relevant top-level YAML
keys, and dispatches to the matching `cmd_run_*` function. Embed /
analyze / report phases are uniform across classes (they go through
`src.main`).
"""
from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
import time
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
CFG_ROOT = REPO / "configs" / "cross_model"
STATUS_CSV = REPO / "data" / "aggregated" / "cross_model_status.csv"


def _entry_class(cfg_path: Path) -> str:
    """Pick the entry-point class for a config.

    Order matters: a perturbation config that runs a dialog
    architecture (`exp_perturb_D1_*`) declares BOTH `dialog:` and
    `perturbation:` keys. We must check `perturbation` first, otherwise
    the dialog runner produces a single `regime=recursive` partition
    instead of the four `control / neutral / lorem / adversarial`
    conditions the perturbation analysis expects."""
    with cfg_path.open(encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    if "perturbation" in cfg:
        return "perturbation"
    if "dialog" in cfg:
        return "dialog"
    return "operator"


def _experiment_id(cfg_path: Path) -> str:
    with cfg_path.open(encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    return cfg.get("experiment_id", cfg_path.stem)


def _load_status() -> dict[tuple[str, str], str]:
    """Map (experiment_id, phase) → status ("done" or last error)."""
    if not STATUS_CSV.exists():
        return {}
    out: dict[tuple[str, str], str] = {}
    with STATUS_CSV.open(encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            out[(row["experiment_id"], row["phase"])] = row["status"]
    return out


def _save_status(status: dict[tuple[str, str], str]) -> None:
    STATUS_CSV.parent.mkdir(parents=True, exist_ok=True)
    rows = sorted(status.items())
    with STATUS_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["experiment_id", "phase", "status"])
        for (exp, phase), st in rows:
            w.writerow([exp, phase, st])


PHASES = ("run", "embed", "analyze", "report")

ENTRY_RUN = {
    "operator":     ["python", "-m", "src.experiments.operators.main"],
    "dialog":       ["python", "-m", "src.experiments.dialog.main"],
    "perturbation": ["python", "-m", "src.experiments.perturbation.main"],
}
ENTRY_OTHER = {
    "operator":     ["python", "-m", "src.main"],
    "dialog":       ["python", "-m", "src.experiments.dialog.main"],
    "perturbation": ["python", "-m", "src.experiments.perturbation.main"],
}
# perturbation/main.py only implements run/embed/analyze; the report phase
# is generic (just renders the standard report.md from the metrics dir),
# so we route it through src.main like operator experiments do.
ENTRY_REPORT_PERTURB = ["python", "-m", "src.main"]


def _cmd_for(phase: str, entry_class: str, cfg_path: Path) -> list[str]:
    if phase == "run":
        base = ENTRY_RUN[entry_class]
    elif phase == "report" and entry_class == "perturbation":
        base = ENTRY_REPORT_PERTURB
    else:
        base = ENTRY_OTHER[entry_class]
    return [*base, "--config", str(cfg_path), phase]


def _experiment_dir(cfg_path: Path) -> Path:
    """Where the pipeline writes data/<experiment_id>/."""
    with cfg_path.open(encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    out_dir = REPO / cfg.get("output_dir", "data") / cfg["experiment_id"]
    return out_dir


def _run_phase(cfg_path: Path, phase: str, entry_class: str,
               dry_run: bool) -> tuple[bool, str]:
    cmd = _cmd_for(phase, entry_class, cfg_path)
    print(f"  $ {' '.join(cmd)}")
    if dry_run:
        return True, "dry-run"
    t0 = time.monotonic()
    try:
        subprocess.run(cmd, check=True, cwd=str(REPO))
        dt = time.monotonic() - t0
    except subprocess.CalledProcessError as e:
        return False, f"exit-{e.returncode}"
    except KeyboardInterrupt:
        raise
    except Exception as e:
        return False, f"err:{type(e).__name__}"
    # Post-condition: the run phase must produce a non-empty steps.jsonl.
    # The dialog/operator runners catch per-step API errors and continue,
    # so a process that exits 0 with zero steps written looks "done" from
    # subprocess but really produced nothing — surface as failure.
    if phase == "run":
        steps_path = _experiment_dir(cfg_path) / "raw" / "steps.jsonl"
        if not steps_path.exists() or steps_path.stat().st_size == 0:
            return False, f"zero-steps after {dt:.0f}s (check API key/balance)"
    return True, f"done ({dt:.0f}s)"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True, help="model tag (e.g. gpt4nano, m2_7)")
    ap.add_argument("--only", default=None,
                    help="run only this exp_* dirname (no .yaml suffix)")
    ap.add_argument("--regex", default=None,
                    help="run only configs matching this experiment_id regex")
    ap.add_argument("--phases", default="run,embed,analyze,report",
                    help="comma-sep subset of run,embed,analyze,report")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true",
                    help="re-run phases already marked done in the status CSV")
    args = ap.parse_args()

    cfg_dir = CFG_ROOT / args.tag
    if not cfg_dir.exists():
        print(f"no config dir {cfg_dir}; run scripts/build_cross_model_configs first")
        return 1

    cfg_paths = sorted(cfg_dir.glob("*.yaml"))
    if args.only:
        cfg_paths = [p for p in cfg_paths if p.stem == args.only]
    if args.regex:
        rx = re.compile(args.regex)
        cfg_paths = [p for p in cfg_paths if rx.search(_experiment_id(p))]
    if not cfg_paths:
        print("no configs match the filters; nothing to do")
        return 0

    phases_to_run = tuple(p.strip() for p in args.phases.split(",") if p.strip())
    for p in phases_to_run:
        if p not in PHASES:
            print(f"unknown phase: {p}; must be one of {PHASES}")
            return 2

    status = _load_status()
    print(f"running {len(cfg_paths)} configs × {len(phases_to_run)} phases "
          f"(tag={args.tag}, dry_run={args.dry_run})")
    n_done = 0; n_skip = 0; n_fail = 0
    try:
        for cfg_path in cfg_paths:
            exp_id = _experiment_id(cfg_path)
            entry_class = _entry_class(cfg_path)
            print(f"\n[{exp_id}] entry={entry_class}")
            for phase in phases_to_run:
                key = (exp_id, phase)
                cur = status.get(key)
                if cur and cur.startswith("done") and not args.force:
                    print(f"  · {phase}: skip ({cur})")
                    n_skip += 1
                    continue
                ok, msg = _run_phase(cfg_path, phase, entry_class, args.dry_run)
                if args.dry_run:
                    continue  # don't persist dry-run state to status csv
                status[key] = ("done " if ok else "fail ") + msg
                _save_status(status)
                if ok:
                    n_done += 1
                else:
                    n_fail += 1
                    print(f"  ✗ {phase}: {msg}; stopping this config (later "
                          "phases depend on this one)")
                    break
    except KeyboardInterrupt:
        print("\ninterrupted; status saved.")

    print(f"\nsummary: {n_done} done, {n_skip} skipped (already done), "
          f"{n_fail} failed")
    print(f"status csv: {STATUS_CSV}")
    return 0 if n_fail == 0 else 3


if __name__ == "__main__":
    raise SystemExit(main())
