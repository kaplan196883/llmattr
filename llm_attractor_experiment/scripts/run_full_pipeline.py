"""
End-to-end pipeline orchestrator (ARTICLE.md §10.4 reproducibility).

Discovers every config under configs/{operators,dialog,perturbation}/*.yaml
and dispatches each to its appropriate runner CLI. Runs are
skip-completed by default (each runner consults its own manifest.json),
so re-invocation is safe and idempotent.

Phases:
    --phase run         only `run` (or equivalent) per runner
    --phase embed       only `embed`
    --phase analyze     only `analyze` (incl. analyze_ext via cmd_analyze)
    --phase report      only `report`
    --phase all         run -> embed -> analyze -> report (default)
    --phase aggregate   only the cross-experiment scripts/aggregate_*.py

Filtering:
    --filter <glob>     restrict to configs whose stem matches the glob,
                        e.g. --filter 'O1*' or --filter 'D2*'

Examples:
    # Full reproduction from scratch (will hit the API a lot — be sure):
    python -m scripts.run_full_pipeline --phase all

    # Only run the analyze phase on every config — useful after a code
    # change to analyze.py / analyze_ext.py:
    python -m scripts.run_full_pipeline --phase analyze

    # Cross-experiment aggregators only (no API calls):
    python -m scripts.run_full_pipeline --phase aggregate
"""
from __future__ import annotations

import argparse
import fnmatch
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


# (configs subdir, runner module)
RUNNER_BY_DIR = {
    "operators": "src.experiments.operators.main",
    "dialog": "src.experiments.dialog.main",
    "perturbation": "src.experiments.perturbation.main",
}

# Cross-experiment aggregators (run after every per-experiment phase).
AGGREGATORS = [
    "scripts.aggregate_basin_predictability",
    "scripts.aggregate_t_sweep",
    "scripts.aggregate_perturbation_cross_regime",
    "scripts.aggregate_dose_response",
    "scripts.aggregate_basin_hardening",
    "scripts.aggregate_o1_d1_t_sensitivity",
]


def discover_configs(filter_glob: str | None = None) -> list[tuple[str, Path]]:
    """Return [(runner_dir, config_path), ...]."""
    found: list[tuple[str, Path]] = []
    configs_root = ROOT / "configs"
    for sub, _runner in RUNNER_BY_DIR.items():
        for p in sorted((configs_root / sub).glob("*.yaml")):
            if filter_glob and not fnmatch.fnmatch(p.stem, filter_glob):
                continue
            found.append((sub, p))
    return found


def run_phase_for_config(runner_dir: str, config: Path, phase: str) -> int:
    """Invoke `python -m <runner> <phase> --config <config>` and return exit code."""
    runner = RUNNER_BY_DIR[runner_dir]
    cmd = [sys.executable, "-m", runner, phase, "--config", str(config)]
    print(f"\n--- [{phase}] {config.relative_to(ROOT)} ---")
    print(f"$ {' '.join(cmd)}")
    t0 = time.time()
    proc = subprocess.run(cmd, cwd=ROOT)
    dt = time.time() - t0
    print(f"--- exit={proc.returncode}  ({dt:.1f}s) ---")
    return proc.returncode


def run_aggregators() -> int:
    """Run every cross-experiment aggregator script in turn. Returns max exit code."""
    rc = 0
    for mod in AGGREGATORS:
        cmd = [sys.executable, "-m", mod]
        print(f"\n--- [aggregate] {mod} ---")
        print(f"$ {' '.join(cmd)}")
        t0 = time.time()
        proc = subprocess.run(cmd, cwd=ROOT)
        dt = time.time() - t0
        print(f"--- exit={proc.returncode}  ({dt:.1f}s) ---")
        rc = max(rc, proc.returncode)
    return rc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="run_full_pipeline")
    parser.add_argument(
        "--phase", default="all",
        choices=["run", "embed", "analyze", "report", "all", "aggregate"],
        help="Pipeline phase to run for every config (default: all).",
    )
    parser.add_argument(
        "--filter", default=None,
        help="Glob restricting configs by stem (e.g., 'O1*' or 'D2*').",
    )
    parser.add_argument(
        "--stop-on-error", action="store_true",
        help="Abort the orchestration on the first failing runner. By default, "
             "failures are logged and the pipeline continues to the next config.",
    )
    args = parser.parse_args(argv)

    if args.phase == "aggregate":
        rc = run_aggregators()
        return rc

    configs = discover_configs(args.filter)
    print(f"discovered {len(configs)} config(s)")
    if not configs:
        print("nothing to do; check --filter")
        return 0

    failed: list[Path] = []
    for runner_dir, cfg in configs:
        rc = run_phase_for_config(runner_dir, cfg, args.phase)
        if rc != 0:
            failed.append(cfg)
            if args.stop_on_error:
                print(f"\nstopping (--stop-on-error) after first failure: {cfg}")
                return rc

    if args.phase == "all":
        # Re-aggregate cross-experiment artefacts so the cross-* CSVs/PNGs
        # reflect the latest per-experiment results.
        run_aggregators()

    if failed:
        print(f"\nFAILED ({len(failed)}):")
        for f in failed:
            print(f"  {f}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
