"""AC1 MVP runner: config -> trajectories -> JSONL.
See docs/AGENTIC_MVP_SPEC.md §2.4, §7.

Enumerates cells (nudge x condition/dose x task x seed), runs each
trajectory through the pluggable-Nudge loop, computes endpoints
(redirect-survival primary; compliance judged on a deterministic
sample; task oracle), and writes:

  data/<experiment_id>/endpoints.jsonl       one row per trajectory
  data/<experiment_id>/trajectories/<run>.json   full per-step trace
  data/<experiment_id>/config_snapshot.yaml

Run:
  python -m src.experiments.agentic.runner configs/agentic/AC1_mvp.yaml --smoke
  python -m src.experiments.agentic.runner configs/agentic/AC1_mvp.yaml
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import yaml

from src.experiments.agentic.agent_client import make_anthropic_client
from src.experiments.agentic.endpoints import (
    Endpoints, redirect_survival, render_final_state,
)
from src.experiments.agentic.inject import make_redirect_injector
from src.experiments.agentic.judge import judge_compliance
from src.experiments.agentic.loop import run_trajectory
from src.experiments.agentic.nudges import build_nudge
from src.experiments.agentic.sandbox import Sandbox, SandboxConfig
from src.experiments.agentic.tasks import Task, load_tasks, run_oracle
from src.experiments.agentic.tools import BASE_TOOLS
from src.utils.logging import get_logger, setup_logging

log = get_logger(__name__)
REPO = Path(__file__).resolve().parents[3]


def _dose_of(condition: str) -> int:
    if condition == "control":
        return 0
    m = "".join(ch for ch in condition if ch.isdigit())
    return int(m) if m else 0


def _sandbox_config(cfg: dict) -> SandboxConfig:
    sb = cfg.get("sandbox", {})
    return SandboxConfig(
        network=sb.get("network", "disabled"),
        bash_timeout_sec=sb.get("bash_timeout_sec", 30),
        bash_output_max_chars=sb.get("bash_output_max_chars", 8000),
        path_jail=sb.get("path_jail", True),
        bash_denylist=tuple(sb.get("bash_denylist", SandboxConfig().bash_denylist)),
    )


def _make_embed_fn(cfg: dict):
    """Lazy embedding fn for the survival cosine fallback (A2 paraphrase).
    Returns None if disabled."""
    surv = cfg.get("endpoints", {}).get("survival", {})
    if surv.get("method") != "cosine_or_verbatim":
        return None
    from src.api.openai_client import make_embedding_client
    client = make_embedding_client()
    model = cfg.get("embedding_model", "text-embedding-3-small")

    def embed_fn(texts: list[str]) -> list[list[float]]:
        resp = client.embeddings.create(model=model, input=texts)
        return [d.embedding for d in resp.data]

    return embed_fn


def _should_judge(run_id: str, dose: int, sample_rate: float) -> bool:
    if dose == 0:
        return False                      # nothing to comply with
    if sample_rate >= 1.0:
        return True
    h = int(hashlib.sha1(run_id.encode()).hexdigest(), 16) % 1000
    return h < sample_rate * 1000


def _run_one(*, cfg, nudge_spec, task: Task, condition: str, seed: int,
             anthropic_client, embed_fn, judge_sample_rate: float) -> dict:
    dose = _dose_of(condition)
    run_id = f"{nudge_spec['id']}__{task.id}__{condition}__seed{seed}"
    nudge = build_nudge(
        nudge_spec, client=anthropic_client,
        summarizer_model=cfg.get("summarizer_model"),
    )
    sandbox = Sandbox.from_seed(task.seed_dir, _sandbox_config(cfg))
    inject_fn = None
    redirect_scaled = None
    inject_step = cfg.get("inject_step", 8) if dose > 0 else None
    if dose > 0:
        inject_fn = make_redirect_injector(task.redirect, dose)
        redirect_scaled = inject_fn.text  # type: ignore[attr-defined]

    try:
        traj = run_trajectory(
            client=anthropic_client,
            model=cfg["agent_model"],
            nudge=nudge,
            sandbox=sandbox,
            goal=task.goal,
            run_id=run_id, task_id=task.id, dose=dose,
            condition=condition, seed=seed,
            tool_names=cfg.get("tools", BASE_TOOLS),
            steps_per_run=cfg.get("steps_per_run", 30),
            inject_step=inject_step,
            inject_fn=inject_fn,
            redirect_text=redirect_scaled,
            max_output_tokens=cfg.get("max_output_tokens", 2048),
            temperature=cfg.get("temperature", 0.8),
        )

        # --- endpoints ---
        task_pass, oracle_detail = run_oracle(task, sandbox)

        if dose > 0:
            surv = redirect_survival(
                traj.final_messages, redirect_scaled,
                embed_fn=embed_fn,
                threshold=cfg.get("endpoints", {}).get("survival", {})
                            .get("paraphrase_threshold", 0.80),
            )
        else:
            surv = {"survived": False, "method": "n/a", "score": None}

        complied = None
        comp_reason = None
        if _should_judge(run_id, dose, judge_sample_rate):
            final_state = render_final_state(sandbox, traj.steps)
            verdict = judge_compliance(
                anthropic_client, cfg.get("judge_model", "claude-sonnet-4-6"),
                task.goal, redirect_scaled, final_state,
            )
            complied = verdict["complied"]
            comp_reason = verdict["reason"]

        endpoints = Endpoints(
            task_pass=task_pass, survived=surv["survived"],
            survival_method=surv["method"], survival_score=surv["score"],
            complied=complied, compliance_reason=comp_reason,
            oracle_detail=oracle_detail.strip().splitlines()[-1] if oracle_detail.strip() else "",
        )
        return _serialize(cfg, traj, endpoints)
    finally:
        sandbox.close()


def _serialize(cfg: dict, traj, endpoints: Endpoints) -> dict:
    injection_fired = any(s.injected for s in traj.steps)
    return {
        "run_id": traj.run_id,
        "experiment_id": cfg["experiment_id"],
        "agent_model": cfg["agent_model"],
        "task_id": traj.task_id,
        "nudge": traj.nudge_id,
        "condition": traj.condition,
        "dose": traj.dose,
        "seed": traj.seed,
        "terminal_step": traj.terminal_step,
        "injection_fired": injection_fired,
        "error": traj.error,
        "redirect_text": traj.redirect_text,
        "endpoints": dataclasses.asdict(endpoints),
        "steps": [dataclasses.asdict(s) for s in traj.steps],
    }


def main(argv=None) -> int:
    setup_logging("INFO")
    ap = argparse.ArgumentParser()
    ap.add_argument("config")
    ap.add_argument("--smoke", action="store_true",
                    help="1 task x all nudges x {control, top dose} x 1 seed")
    ap.add_argument("--limit", type=int, default=0, help="cap number of cells")
    ap.add_argument("--no-judge", action="store_true",
                    help="skip compliance judging entirely")
    ap.add_argument("--workers", type=int, default=0,
                    help="override parallel_trajectories")
    ap.add_argument("--inject-step", type=int, default=None,
                    help="override inject_step (useful for smoke runs)")
    args = ap.parse_args(argv)

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    if args.inject_step is not None:
        cfg["inject_step"] = args.inject_step
    tasks = load_tasks(cfg)
    nudges = cfg["nudges"]
    conditions = cfg["perturbation"]["conditions"]
    n_seeds = cfg.get("runs_per_condition", 4)

    if args.smoke:
        tasks = tasks[:1]
        top = [c for c in conditions if c != "control"][-1:]
        conditions = ["control"] + top
        n_seeds = 1

    judge_sample_rate = 0.0 if args.no_judge else (
        cfg.get("endpoints", {}).get("compliance", {}).get("sample_rate", 0.25))

    # Build the cell list
    cells = []
    for nudge_spec in nudges:
        for task in tasks:
            for condition in conditions:
                for seed in range(n_seeds):
                    cells.append((nudge_spec, task, condition, seed))
    if args.limit:
        cells = cells[:args.limit]

    out_dir = REPO / cfg.get("output_dir", "data") / cfg["experiment_id"]
    (out_dir / "trajectories").mkdir(parents=True, exist_ok=True)
    (out_dir / "config_snapshot.yaml").write_text(
        yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
    endpoints_path = out_dir / "endpoints.jsonl"

    anthropic_client = make_anthropic_client()
    embed_fn = _make_embed_fn(cfg)

    workers = args.workers or cfg.get("parallel_trajectories", 8)
    log.info("running %d cells across %d workers -> %s",
             len(cells), workers, out_dir)

    results: list[dict] = []
    with endpoints_path.open("w", encoding="utf-8") as ep_f:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = {
                ex.submit(
                    _run_one, cfg=cfg, nudge_spec=ns, task=tk,
                    condition=cd, seed=sd,
                    anthropic_client=anthropic_client, embed_fn=embed_fn,
                    judge_sample_rate=judge_sample_rate,
                ): (ns["id"], tk.id, cd, sd)
                for (ns, tk, cd, sd) in cells
            }
            done = 0
            for fut in as_completed(futs):
                key = futs[fut]
                try:
                    rec = fut.result()
                except Exception as exc:
                    log.error("cell %s failed: %s", key, exc)
                    done += 1
                    continue
                results.append(rec)
                # full trajectory
                (out_dir / "trajectories" / f"{rec['run_id']}.json").write_text(
                    json.dumps(rec, indent=2), encoding="utf-8")
                # endpoints row (without the heavy steps payload)
                row = {k: v for k, v in rec.items() if k != "steps"}
                ep_f.write(json.dumps(row) + "\n")
                ep_f.flush()
                done += 1
                e = rec["endpoints"]
                log.info("[%d/%d] %s  pass=%s surv=%s(%s) comp=%s",
                         done, len(cells), rec["run_id"],
                         e["task_pass"], e["survived"], e["survival_method"],
                         e["complied"])

    _print_summary(results)
    log.info("wrote %s (%d rows)", endpoints_path, len(results))
    return 0


def _print_summary(results: list[dict]) -> None:
    """Quick redirect-survival-by-(nudge,dose) table to eyeball the gate."""
    from collections import defaultdict
    agg = defaultdict(lambda: [0, 0])   # (nudge,dose) -> [survived, total]
    passes = defaultdict(lambda: [0, 0])
    skipped = 0
    for r in results:
        if r["dose"] == 0:
            continue
        # Only count runs where the redirect actually fired (the agent
        # had not already terminated before inject_step).
        if not r.get("injection_fired", True):
            skipped += 1
            continue
        key = (r["nudge"], r["dose"])
        agg[key][1] += 1
        agg[key][0] += int(r["endpoints"]["survived"])
        passes[r["nudge"]][1] += 1
        passes[r["nudge"]][0] += int(r["endpoints"]["task_pass"])
    if skipped:
        print(f"\n[note] {skipped} dose>0 runs excluded (agent terminated "
              f"before inject_step; redirect never fired)")
    print("\n=== redirect-survival by (nudge, dose) ===")
    for key in sorted(agg):
        s, n = agg[key]
        print(f"  {key[0]:22s} dose={key[1]:4d}  survived {s}/{n} = {s/n:.0%}" if n else "")
    print("=== task-pass by nudge (all conditions) ===")
    for nudge in sorted(passes):
        s, n = passes[nudge]
        print(f"  {nudge:22s}  pass {s}/{n} = {s/n:.0%}" if n else "")


if __name__ == "__main__":
    sys.exit(main())
