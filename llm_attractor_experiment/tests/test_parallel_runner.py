"""
Smoke tests for ThreadPoolExecutor-based parallel trajectory execution.
Validates:
  - correctness (same set of step records produced as sequential)
  - thread safety of manifest + JSONL sink
  - parallel_trajectories=1 is equivalent to pre-parallel behavior
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from src import config as config_mod
from src.api.generator import GenerationResult
from src.experiments.operators import main as op_main
from src.experiments.operators import trajectory as op_traj


def _tiny_config(tmp_path: Path, experiment_id: str, parallel_n: int) -> Path:
    cfg = {
        "experiment_id": experiment_id,
        "generation_model": "fake-gen",
        "embedding_model": "fake-embed",
        "steps_per_run": 4,
        "runs_per_condition": 2,
        "initial_conditions_per_family": 2,
        "max_output_tokens": 32,
        "temperature": 0.7,
        "top_p": 1.0,
        "include_logprobs": False,
        "clip_rule": "tail_chars",
        "max_context_chars": 400,
        "rolling_window_k": 3,
        "context_tail_chars": 200,
        "context_full_chars": 400,
        "observables": ["output"],
        "pca_dims": [2],
        "clustering": {"method": "kmeans", "kmeans": {"n_clusters": 2}, "dbscan": {"eps": 0.3, "min_samples": 2}},
        "recurrence": {"metric": "cosine", "epsilon": 0.3, "tau": 2},
        "dwell": {"space": "pca2"},
        "basin": {"target_region_late_fraction": 0.5, "target_step_fraction": 0.5, "perturbations": ["seed_only"]},
        "baseline_modes": [],
        "batch_embeddings": False,
        "use_evals": False,
        "seed": 1,
        "parallel_trajectories": parallel_n,
        "output_dir": str(tmp_path),
        "loop_mode": "append",
        "prompt_families": [
            {
                "name": "f1",
                "system_prompt": "continue",
                "initial_conditions": ["seed-alpha", "seed-beta"],
            },
            {
                "name": "f2",
                "system_prompt": "continue",
                "initial_conditions": ["seed-gamma", "seed-delta"],
            },
        ],
    }
    p = tmp_path / f"{experiment_id}.yaml"
    p.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    return p


@pytest.fixture
def fake_gen(monkeypatch):
    def _make():
        call_count = {"n": 0}

        def fake_generate_step(client, context_text, config, system_prompt=None, **kwargs):
            call_count["n"] += 1
            # Deterministic-ish output keyed off context content length
            out = f" out{len(context_text) % 97}"
            return GenerationResult(
                output_text=out,
                model="fake-gen",
                response_id=f"fake-{call_count['n']}",
                latency_sec=0.0,
                retries=0,
                raw={"fake": True},
                logprobs=None,
            )

        monkeypatch.setattr(op_traj, "generate_step", fake_generate_step)

        def fake_make_client():
            return object()

        monkeypatch.setattr(op_main, "make_client", fake_make_client)
        return call_count

    return _make()


def test_parallel_4_produces_same_step_count_as_serial(tmp_path, fake_gen):
    cfg_path = _tiny_config(tmp_path, "exp_serial", parallel_n=1)
    cfg = config_mod.load_config(cfg_path)
    op_main.cmd_run_op(cfg)

    cfg_path2 = _tiny_config(tmp_path, "exp_parallel", parallel_n=4)
    cfg2 = config_mod.load_config(cfg_path2)
    op_main.cmd_run_op(cfg2)

    serial_records = _load_steps(tmp_path / "exp_serial" / "raw" / "steps.jsonl")
    parallel_records = _load_steps(tmp_path / "exp_parallel" / "raw" / "steps.jsonl")

    # Both runs should produce the same number of (family, ic, run, step) tuples.
    serial_keys = sorted(
        (r["prompt_family"], r["initial_condition_id"], r["run_id"], r["step"])
        for r in serial_records
    )
    parallel_keys = sorted(
        (r["prompt_family"], r["initial_condition_id"], r["run_id"], r["step"])
        for r in parallel_records
    )
    assert serial_keys == parallel_keys, "parallel run missed or duplicated trajectories"
    # Plan: 2 families × 2 ICs × 2 runs × 4 steps = 32 records
    assert len(serial_records) == 32
    assert len(parallel_records) == 32


def test_parallel_manifest_marks_all_completed(tmp_path, fake_gen):
    cfg_path = _tiny_config(tmp_path, "exp_manifest", parallel_n=4)
    cfg = config_mod.load_config(cfg_path)
    op_main.cmd_run_op(cfg)
    manifest_path = tmp_path / "exp_manifest" / "raw" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    # 2 families × 2 ICs × 2 runs = 8 recursive entries, plus no baseline_modes
    completed = [k for k, v in manifest.items() if v.get("status") == "completed"]
    assert len(completed) == 8


def test_parallel_resume_skips_completed(tmp_path, fake_gen):
    cfg_path = _tiny_config(tmp_path, "exp_resume", parallel_n=4)
    cfg = config_mod.load_config(cfg_path)
    # first run
    op_main.cmd_run_op(cfg)
    first_count = fake_gen["n"]
    # second run should skip everything
    op_main.cmd_run_op(cfg)
    second_count = fake_gen["n"]
    # No extra generations should have happened the second time.
    assert second_count == first_count


def _load_steps(path: Path) -> list[dict]:
    out = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out
