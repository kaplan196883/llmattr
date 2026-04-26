"""
Entry point for operator experiments. Separate from src/main.py so the original
pipeline stays untouched.

CLI:
    python -m src.experiments.operators.main run     --config configs/operators/O1_continue.yaml
    python -m src.experiments.operators.main embed   --config configs/operators/O1_continue.yaml
    python -m src.experiments.operators.main analyze --config configs/operators/O1_continue.yaml
    python -m src.experiments.operators.main report  --config configs/operators/O1_continue.yaml
    python -m src.experiments.operators.main all     --config configs/operators/O1_continue.yaml
    python -m src.experiments.operators.main resume  --config configs/operators/O1_continue.yaml

Reads `loop_mode` from the YAML's raw_dict (field not part of base Config dataclass).
Run phase uses the isolated run_trajectory_op; embed/analyze/report are delegated
to the original src.main for reuse.
"""
from __future__ import annotations

import argparse
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from src.api.openai_client import make_client
from src.config import Config, PromptFamily, limit_initial_conditions, load_config, save_config_snapshot
from src.core.baselines import independent_regeneration_provider, no_feedback_provider
from src.core.trajectory import RunIds
from src.core.trajectory import make_locked_jsonl_sink
from src.experiments.operators.trajectory import run_trajectory_op
from src.main import cmd_analyze, cmd_embed, cmd_report, STEPS_FILE, MANIFEST_FILE, _prune_uncommitted_steps
from src.utils.io import ensure_dir, read_json, write_json
from src.utils.logging import get_logger, setup_logging
from src.utils.seeds import set_global_seed

log = get_logger(__name__)


def _loop_mode(cfg: Config) -> str:
    return str(cfg.raw_dict.get("loop_mode", "append"))


# ---------------------------- RUN (generation, operator-aware) -----------------


def cmd_run_op(cfg: Config) -> None:
    set_global_seed(cfg.seed)
    client = make_client()
    loop_mode = _loop_mode(cfg)
    log.info("operator experiment: loop_mode=%s, experiment_id=%s", loop_mode, cfg.experiment_id)

    ensure_dir(cfg.experiment_dir)
    save_config_snapshot(cfg, cfg.experiment_dir / "config.yaml")
    ensure_dir(cfg.raw_dir)

    steps_path = cfg.raw_dir / STEPS_FILE
    manifest_path = cfg.raw_dir / MANIFEST_FILE
    manifest = _load_manifest(manifest_path)
    _prune_uncommitted_steps(steps_path, manifest)
    # locked_sink wraps the JSONL writer with a Lock so concurrent worker
    # threads can't interleave writes; manifest_lock is separate because it
    # also covers in-memory mutations + atomic writeback.
    locked_sink = make_locked_jsonl_sink(steps_path)
    manifest_lock = threading.Lock()

    planned = _plan_runs(cfg)
    log.info("planned %d trajectories", len(planned))

    parallel_n = max(1, int(cfg.parallel_trajectories))

    def _worker(run_spec: dict) -> tuple[str, str]:
        run_key = run_spec["run_key"]
        with manifest_lock:
            if manifest.get(run_key, {}).get("status") == "completed":
                return run_key, "skipped"
        try:
            _execute_run(client, cfg, run_spec, locked_sink, loop_mode)
            with manifest_lock:
                manifest[run_key] = {
                    "status": "completed",
                    "timestamp": time.time(),
                    "steps": cfg.steps_per_run,
                    "loop_mode": loop_mode,
                }
                write_json(manifest_path, manifest)
            return run_key, "completed"
        except Exception as exc:
            log.exception("run %s failed: %s", run_key, exc)
            with manifest_lock:
                manifest[run_key] = {
                    "status": "failed",
                    "timestamp": time.time(),
                    "error": str(exc),
                }
                write_json(manifest_path, manifest)
            return run_key, "failed"

    if parallel_n == 1:
        for spec in planned:
            _worker(spec)
    else:
        log.info("running with parallel_trajectories=%d", parallel_n)
        with ThreadPoolExecutor(max_workers=parallel_n) as executor:
            futures = {executor.submit(_worker, spec): spec["run_key"] for spec in planned}
            completed = 0
            for fut in as_completed(futures):
                _key, status = fut.result()
                completed += 1
                if completed % 20 == 0 or completed == len(futures):
                    log.info("parallel progress: %d/%d trajectories finished", completed, len(futures))

    log.info("run phase done. steps at %s", steps_path)


def _plan_runs(cfg: Config) -> list[dict]:
    planned: list[dict] = []
    for family in cfg.prompt_families:
        ics = limit_initial_conditions(family, cfg.initial_conditions_per_family)
        for ic_idx, ic_text in enumerate(ics):
            ic_id = f"ic_{ic_idx:03d}"
            for run_idx in range(cfg.runs_per_condition):
                run_id = f"run_{run_idx:03d}"
                planned.append(
                    {
                        "run_key": f"recursive|{family.name}|{ic_id}|{run_id}",
                        "regime": "recursive",
                        "family": family,
                        "ic_id": ic_id,
                        "ic_text": ic_text,
                        "run_id": run_id,
                    }
                )
                for mode in cfg.baseline_modes:
                    planned.append(
                        {
                            "run_key": f"{mode}|{family.name}|{ic_id}|{run_id}",
                            "regime": mode,
                            "family": family,
                            "ic_id": ic_id,
                            "ic_text": ic_text,
                            "run_id": run_id,
                        }
                    )
    return planned


def _execute_run(client, cfg: Config, spec: dict, sink, loop_mode: str) -> None:
    family: PromptFamily = spec["family"]
    regime: str = spec["regime"]
    ids = RunIds(
        experiment_id=cfg.experiment_id,
        prompt_family=family.name,
        initial_condition_id=spec["ic_id"],
        run_id=spec["run_id"],
        regime=regime,
    )

    provider = None
    if regime == "no_feedback":
        provider = no_feedback_provider()
    elif regime == "independent_regeneration":
        provider = independent_regeneration_provider(family.system_prompt)
    elif regime == "time_shuffled":
        log.debug("skipping generation for post-hoc time_shuffled baseline")
        return
    elif regime != "recursive":
        log.warning("unknown regime '%s' -> treating as recursive", regime)

    run_trajectory_op(
        client,
        initial_context=spec["ic_text"],
        config=cfg,
        ids=ids,
        loop_mode=loop_mode,
        system_prompt=family.system_prompt,
        step_sink=sink,
        context_provider=provider,
    )


def _load_manifest(path: Path) -> dict:
    if path.exists():
        try:
            return read_json(path)
        except Exception:
            pass
    return {}


# ---------------------------- CLI ------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="operator_experiment")
    parser.add_argument(
        "command",
        choices=["run", "embed", "analyze", "report", "all", "resume"],
    )
    parser.add_argument("--config", required=True)
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)

    cfg = load_config(args.config)
    log_file = cfg.experiment_dir / "run.log"
    ensure_dir(log_file.parent)
    setup_logging(args.log_level, log_file)

    if args.command == "run":
        cmd_run_op(cfg)
    elif args.command == "resume":
        cmd_run_op(cfg)
    elif args.command == "embed":
        cmd_embed(cfg)
    elif args.command == "analyze":
        cmd_analyze(cfg)
    elif args.command == "report":
        cmd_report(cfg)
    elif args.command == "all":
        cmd_run_op(cfg)
        cmd_embed(cfg)
        cmd_analyze(cfg)
        cmd_report(cfg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
