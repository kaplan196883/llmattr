"""
Driver for the perturbation-response experiment.

Reuses a D1-style dialog config and layers on a perturbation block:

  perturbation:
    enabled: true
    override_step: 15
    adversarial_source_experiment: exp_pub_D1_dialog_curious_helpful_v2
    conditions: [control, neutral, lorem, adversarial]

Per (family, ic, run) tuple, runs four trajectories — one per condition —
all with identical seed prefix but different perturbation at override_step.
Condition is encoded in the `regime` field so the downstream embed pipeline
treats each as its own "regime" and produces separate PCA/cluster artefacts.

CLI:
    python -u -m src.experiments.perturbation.main run --config configs/perturbation/pilot.yaml
"""
from __future__ import annotations

import argparse
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from src.api.openai_client import make_generation_client
from src.config import Config, PromptFamily, limit_initial_conditions, load_config, save_config_snapshot
from src.core.trajectory import RunIds
from src.experiments.dialog.main import _load_manifest, _roles_from_cfg, _loop_mode
from src.experiments.dialog.main import cmd_embed_dialog, STEPS_FILE, MANIFEST_FILE
from src.core.trajectory import make_locked_jsonl_sink
from src.experiments.dialog.trajectory import Role
from src.experiments.perturbation.corpora import (
    neutral_wiki, random_words, sample_adversarial_text,
)
from src.experiments.perturbation.runner import run_perturbed_dialog_trajectory
from src.experiments.perturbation.runner_op import run_perturbed_trajectory_op
from src.main import _prune_uncommitted_steps, cmd_embed
from src.utils.io import ensure_dir, write_json
from src.utils.logging import get_logger, setup_logging
from src.utils.seeds import set_global_seed

log = get_logger(__name__)


def _perturb_cfg(cfg: Config) -> dict:
    p = cfg.raw_dict.get("perturbation") or {}
    if not p.get("enabled", False):
        raise ValueError("config missing or disabled 'perturbation' block")
    return p


def _plan_runs(cfg: Config, conditions: list[str]) -> list[dict]:
    planned: list[dict] = []
    for family in cfg.prompt_families:
        ics = limit_initial_conditions(family, cfg.initial_conditions_per_family)
        for ic_idx, ic_text in enumerate(ics):
            ic_id = f"ic_{ic_idx:03d}"
            for run_idx in range(cfg.runs_per_condition):
                run_id = f"run_{run_idx:03d}"
                for cond in conditions:
                    planned.append({
                        "run_key": f"{cond}|{family.name}|{ic_id}|{run_id}",
                        "condition": cond,
                        "family": family,
                        "ic_id": ic_id,
                        "ic_text": ic_text,
                        "run_id": run_id,
                    })
    return planned


def _parse_dose_condition(condition: str) -> tuple[str, int | None]:
    """Split a condition string into (base_type, dose).

    'neutral' -> ('neutral', None)
    'neutral_dose40' -> ('neutral', 40)
    'lorem_dose120' -> ('lorem', 120)
    """
    if "_dose" in condition:
        base, _, rest = condition.partition("_dose")
        try:
            return base, int(rest)
        except ValueError:
            pass
    return condition, None


def _resolve_perturbation_text(
    condition: str,
    family_name: str,
    source_exp_dir: Path | None,
    run_seed: int,
    is_dialog: bool = True,
    agent_role: str = "agent",
) -> str | None:
    if condition == "control":
        return None
    base, dose = _parse_dose_condition(condition)
    if base == "neutral":
        return neutral_wiki(seed=run_seed, approx_tokens=dose)
    if base == "lorem":
        # Convert dose (tokens) to n_words (~1.3 words/token for these short nouns)
        n_words = max(5, int(dose / 1.3)) if dose is not None else 70
        return random_words(n_words=n_words, seed=run_seed)
    if base == "adversarial":
        if source_exp_dir is None or not source_exp_dir.exists():
            raise ValueError(
                f"adversarial condition requires adversarial_source_experiment; "
                f"missing or not found: {source_exp_dir}"
            )
        # For dialog: restrict to responder role (agent / expert / role_b).
        # For operators: any role/none.
        role = agent_role if is_dialog else None
        text = sample_adversarial_text(
            source_experiment_dir=source_exp_dir,
            exclude_family=family_name,
            min_step=20,
            role=role,
            seed=run_seed,
        )
        if dose is not None:
            target_chars = dose * 4
            if len(text) > target_chars:
                cut = text[:target_chars]
                last_space = cut.rfind(" ")
                if last_space > target_chars // 2:
                    cut = cut[:last_space]
                text = cut.rstrip(",;: ") + "."
        return text
    raise ValueError(f"unknown perturbation condition: {condition}")


def _is_dialog_config(cfg: Config) -> bool:
    return bool(cfg.raw_dict.get("dialog"))


def cmd_run(cfg: Config) -> None:
    set_global_seed(cfg.seed)
    client = make_generation_client(cfg.generation_provider)
    is_dialog = _is_dialog_config(cfg)
    if is_dialog:
        role_a, role_b, initiator = _roles_from_cfg(cfg)
    else:
        role_a = role_b = initiator = None
    loop_mode = _loop_mode(cfg)
    pblock = _perturb_cfg(cfg)
    override_step = int(pblock["override_step"])
    conditions = list(pblock.get("conditions", ["control", "neutral", "lorem", "adversarial"]))
    source_exp = pblock.get("adversarial_source_experiment")
    source_exp_dir = Path("data") / source_exp if source_exp else None

    log.info(
        "perturbation experiment: override_step=%d, conditions=%s, source=%s",
        override_step, conditions, source_exp,
    )
    ensure_dir(cfg.experiment_dir)
    save_config_snapshot(cfg, cfg.experiment_dir / "config.yaml")
    ensure_dir(cfg.raw_dir)

    steps_path = cfg.raw_dir / STEPS_FILE
    manifest_path = cfg.raw_dir / MANIFEST_FILE
    manifest = _load_manifest(manifest_path)
    _prune_uncommitted_steps(steps_path, manifest)
    locked_sink = make_locked_jsonl_sink(steps_path)
    manifest_lock = threading.Lock()

    planned = _plan_runs(cfg, conditions)
    log.info("planned %d trajectories (%d conditions × %d base)", len(planned),
             len(conditions), len(planned) // len(conditions))

    parallel_n = max(1, int(cfg.parallel_trajectories))

    def _worker(spec: dict) -> tuple[str, str]:
        run_key = spec["run_key"]
        with manifest_lock:
            if manifest.get(run_key, {}).get("status") == "completed":
                return run_key, "skipped"
        try:
            family: PromptFamily = spec["family"]
            condition = spec["condition"]
            # Per-trajectory seed so perturbation text is reproducible per run
            per_run_seed = hash((cfg.seed, family.name, spec["ic_id"], spec["run_id"], condition)) & 0xFFFFFFFF
            pert_text = _resolve_perturbation_text(
                condition, family.name, source_exp_dir, per_run_seed,
                is_dialog=is_dialog,
                agent_role=(role_b.name if role_b is not None else "agent"),
            )
            ids = RunIds(
                experiment_id=cfg.experiment_id,
                prompt_family=family.name,
                initial_condition_id=spec["ic_id"],
                run_id=spec["run_id"],
                regime=condition,   # encode condition as regime for downstream
            )
            if is_dialog:
                run_perturbed_dialog_trajectory(
                    client=client,
                    seed_utterance=spec["ic_text"],
                    config=cfg,
                    ids=ids,
                    role_a=role_a,
                    role_b=role_b,
                    perturbation_condition=condition,
                    perturbation_text=pert_text,
                    override_step=override_step,
                    initiator=initiator,
                    loop_mode=loop_mode,
                    step_sink=locked_sink,
                )
            else:
                run_perturbed_trajectory_op(
                    client=client,
                    initial_context=spec["ic_text"],
                    config=cfg,
                    ids=ids,
                    perturbation_condition=condition,
                    perturbation_text=pert_text,
                    override_step=override_step,
                    loop_mode=loop_mode,
                    system_prompt=family.system_prompt,
                    step_sink=locked_sink,
                )
            with manifest_lock:
                manifest[run_key] = {
                    "status": "completed",
                    "timestamp": time.time(),
                    "steps": cfg.steps_per_run,
                    "condition": condition,
                    "override_step": override_step,
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
                _key, _status = fut.result()
                completed += 1
                if completed % 10 == 0 or completed == len(futures):
                    log.info("parallel progress: %d/%d trajectories finished", completed, len(futures))

    log.info("run phase done. steps at %s", steps_path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="perturbation_experiment")
    parser.add_argument("command", choices=["run", "embed", "analyze", "all"])
    parser.add_argument("--config", required=True)
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)

    cfg = load_config(args.config)
    log_file = cfg.experiment_dir / "run.log"
    ensure_dir(log_file.parent)
    setup_logging(args.log_level, log_file)

    is_dialog = _is_dialog_config(cfg)
    if args.command == "run":
        cmd_run(cfg)
    elif args.command == "embed":
        if is_dialog:
            cmd_embed_dialog(cfg)
        else:
            cmd_embed(cfg)
    elif args.command == "analyze":
        from src.experiments.perturbation.analyze import cmd_analyze_perturbation
        cmd_analyze_perturbation(cfg, is_dialog=is_dialog)
    elif args.command == "all":
        cmd_run(cfg)
        if is_dialog:
            cmd_embed_dialog(cfg)
        else:
            cmd_embed(cfg)
        from src.experiments.perturbation.analyze import cmd_analyze_perturbation
        cmd_analyze_perturbation(cfg, is_dialog=is_dialog)
    return 0


if __name__ == "__main__":
    sys.exit(main())
