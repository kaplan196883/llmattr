"""
Entry point for dialog experiments (two LLMs conversing).

Config schema extension (read from cfg.raw_dict):
    dialog:
      role_a:
        name: user
        system_prompt: "..."
      role_b:
        name: agent
        system_prompt: "..."
      initiator: role_b      # which role generates first; default role_b
    loop_mode: append         # or replace

Uses existing cfg.prompt_families[*].initial_conditions as seed utterances;
family-level system_prompt is ignored in dialog mode.

CLI:
    python -m src.experiments.dialog.main all --config configs/dialog/D1_curious_helpful.yaml
"""
from __future__ import annotations

import argparse
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

from src.api.embedder import embed_texts
from src.api.openai_client import make_client
from src.config import Config, PromptFamily, limit_initial_conditions, load_config, save_config_snapshot
from src.core.trajectory import RunIds
from src.experiments.dialog.observables import build_dialog_observables
from src.experiments.dialog.trajectory import Role, make_jsonl_sink, run_dialog_trajectory
from src.main import cmd_analyze, cmd_report, STEPS_FILE, MANIFEST_FILE
from src.utils.io import ensure_dir, read_json, read_jsonl, save_npy, write_json, write_parquet
from src.utils.logging import get_logger, setup_logging
from src.utils.seeds import set_global_seed

log = get_logger(__name__)


def _dialog_cfg(cfg: Config) -> dict:
    d = cfg.raw_dict.get("dialog") or {}
    if not d:
        raise ValueError("config missing top-level 'dialog' block")
    return d


def _roles_from_cfg(cfg: Config) -> tuple[Role, Role, str]:
    d = _dialog_cfg(cfg)
    ra = d.get("role_a") or {}
    rb = d.get("role_b") or {}
    for name, block in [("role_a", ra), ("role_b", rb)]:
        if not block.get("name") or not block.get("system_prompt"):
            raise ValueError(f"dialog.{name} needs `name` and `system_prompt`")
    initiator = d.get("initiator", "role_b")
    return (
        Role(name=ra["name"], system_prompt=ra["system_prompt"]),
        Role(name=rb["name"], system_prompt=rb["system_prompt"]),
        initiator,
    )


def _loop_mode(cfg: Config) -> str:
    return str(cfg.raw_dict.get("loop_mode", "append"))


# ---------------------------- RUN (dialog) -----------------------------------


def cmd_run_dialog(cfg: Config) -> None:
    set_global_seed(cfg.seed)
    client = make_client()
    role_a, role_b, initiator = _roles_from_cfg(cfg)
    loop_mode = _loop_mode(cfg)

    log.info(
        "dialog experiment: loop_mode=%s, initiator=%s, role_a=%s, role_b=%s",
        loop_mode,
        initiator,
        role_a.name,
        role_b.name,
    )
    ensure_dir(cfg.experiment_dir)
    save_config_snapshot(cfg, cfg.experiment_dir / "config.yaml")
    ensure_dir(cfg.raw_dir)

    steps_path = cfg.raw_dir / STEPS_FILE
    manifest_path = cfg.raw_dir / MANIFEST_FILE
    manifest = _load_manifest(manifest_path)
    raw_sink = make_jsonl_sink(steps_path)

    sink_lock = threading.Lock()
    manifest_lock = threading.Lock()

    def locked_sink(rec: dict) -> None:
        with sink_lock:
            raw_sink(rec)

    planned = _plan_runs(cfg)
    log.info("planned %d trajectories", len(planned))

    parallel_n = max(1, int(cfg.parallel_trajectories))

    def _worker(spec: dict) -> tuple[str, str]:
        run_key = spec["run_key"]
        with manifest_lock:
            if manifest.get(run_key, {}).get("status") == "completed":
                return run_key, "skipped"
        try:
            _execute_run(client, cfg, spec, locked_sink, role_a, role_b, initiator, loop_mode)
            with manifest_lock:
                manifest[run_key] = {
                    "status": "completed",
                    "timestamp": time.time(),
                    "steps": cfg.steps_per_run,
                    "loop_mode": loop_mode,
                    "initiator": initiator,
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
                # baselines for dialog:
                # - time_shuffled is post-hoc; no gen call needed
                # - no_feedback / independent_regeneration aren't meaningful in two-agent setup,
                #   so we skip them unless explicitly listed.
                for mode in cfg.baseline_modes:
                    if mode == "time_shuffled":
                        continue
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


def _execute_run(client, cfg, spec, sink, role_a, role_b, initiator, loop_mode) -> None:
    family: PromptFamily = spec["family"]
    regime: str = spec["regime"]
    ids = RunIds(
        experiment_id=cfg.experiment_id,
        prompt_family=family.name,
        initial_condition_id=spec["ic_id"],
        run_id=spec["run_id"],
        regime=regime,
    )
    if regime != "recursive":
        # Dialog mode currently only supports recursive; skip other regimes.
        log.debug("dialog skipping non-recursive regime '%s'", regime)
        return
    run_dialog_trajectory(
        client=client,
        seed_utterance=spec["ic_text"],
        config=cfg,
        ids=ids,
        role_a=role_a,
        role_b=role_b,
        initiator=initiator,
        loop_mode=loop_mode,
        step_sink=sink,
    )


# ---------------------------- EMBED (dialog-aware) -------------------------


def cmd_embed_dialog(cfg: Config) -> None:
    """
    Embed observables for a dialog experiment. Uses build_dialog_observables
    so role-separated observables (last_user_turn, rolling_agent_k3, turn_pair, …)
    are supported alongside the generic ones (output, rolling_k3, context_tail).
    """
    client = make_client()
    steps_path = cfg.raw_dir / STEPS_FILE
    if not steps_path.exists():
        raise FileNotFoundError(f"no step log at {steps_path}; run `run` first")

    steps = list(read_jsonl(steps_path))
    log.info("loaded %d step records", len(steps))
    df = pd.DataFrame(steps)
    if df.empty:
        raise RuntimeError("no step records to embed")

    # Extract per-family seed (initial_condition text). We need the seed to use
    # as fallback at early steps where a role hasn't spoken yet. We recover it
    # from the first step's `context_before` field: the trajectory starts with
    # the seed formatted as role_a's opener, which is also in the first
    # context sent to the model.
    seed_by_ic: dict[tuple, str] = {}
    for r in steps:
        key = (r["prompt_family"], r["initial_condition_id"])
        if key not in seed_by_ic and r["step"] == 0:
            # Strip the role label that trajectory.py prepends.
            ctx = r.get("context_before", "")
            if ctx.startswith("["):
                # remove "[User]: " prefix and trailing whitespace
                bracket_end = ctx.find("]:")
                if bracket_end != -1:
                    ctx = ctx[bracket_end + 2 :].strip()
            seed_by_ic[key] = ctx

    for obs_name in cfg.observables:
        _embed_observable_dialog(client, cfg, df, obs_name, seed_by_ic)

    log.info("embedding phase done")


def _embed_observable_dialog(
    client, cfg: Config, steps_df: pd.DataFrame, obs_name: str, seed_by_ic: dict
) -> None:
    group_cols = ["regime", "prompt_family", "initial_condition_id", "run_id"]
    steps_df = steps_df.sort_values(group_cols + ["step"]).reset_index(drop=True)

    all_texts: list[str] = []
    all_meta_rows: list[dict] = []
    for _, sub in steps_df.groupby(group_cols, dropna=False):
        sub = sub.sort_values("step")
        sub_records = sub.to_dict(orient="records")
        if not sub_records:
            continue
        seed_key = (sub_records[0]["prompt_family"], sub_records[0]["initial_condition_id"])
        seed_utterance = seed_by_ic.get(seed_key, "")
        built = build_dialog_observables(
            sub_records,
            [obs_name],
            k=cfg.rolling_window_k,
            tail_chars=cfg.context_tail_chars,
            full_chars=cfg.context_full_chars,
            seed_utterance=seed_utterance,
        )
        texts = built[obs_name]
        for rec, t in zip(sub_records, texts):
            all_texts.append(t)
            all_meta_rows.append(
                {
                    "regime": rec["regime"],
                    "prompt_family": rec["prompt_family"],
                    "initial_condition_id": rec["initial_condition_id"],
                    "run_id": rec["run_id"],
                    "step": rec["step"],
                    "role": rec.get("role", ""),
                    "text_len": len(t),
                }
            )

    log.info("embedding %d texts for observable '%s'", len(all_texts), obs_name)
    vecs = embed_texts(client, all_texts, cfg)
    if vecs.shape[0] == 0:
        log.warning("no vectors produced for observable %s", obs_name)
        return

    obs_dir = cfg.embeddings_dir / obs_name
    ensure_dir(obs_dir)
    save_npy(obs_dir / "embeddings.npy", vecs)
    meta_df = pd.DataFrame(all_meta_rows)
    write_parquet(obs_dir / "metadata.parquet", meta_df)
    log.info("wrote embeddings (%s) to %s", vecs.shape, obs_dir)


def _load_manifest(path: Path) -> dict:
    if path.exists():
        try:
            return read_json(path)
        except Exception:
            pass
    return {}


# ---------------------------- CLI ------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dialog_experiment")
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

    if args.command in ("run", "resume"):
        cmd_run_dialog(cfg)
    elif args.command == "embed":
        cmd_embed_dialog(cfg)
    elif args.command == "analyze":
        cmd_analyze(cfg)
    elif args.command == "report":
        cmd_report(cfg)
    elif args.command == "all":
        cmd_run_dialog(cfg)
        cmd_embed_dialog(cfg)
        cmd_analyze(cfg)
        cmd_report(cfg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
