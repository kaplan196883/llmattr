"""
End-to-end smoke test using a tiny config. Monkeypatches the OpenAI generator
and embedder so the test runs offline.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import yaml

from src import main as cli
from src.api import embedder as embedder_mod
from src.api import openai_client as client_mod
from src.api.generator import GenerationResult
from src.core import trajectory as trajectory_mod


def _write_tiny_config(tmp_path: Path) -> Path:
    cfg = {
        "experiment_id": "exp_test",
        "generation_model": "fake-gen",
        "embedding_model": "fake-embed",
        "steps_per_run": 6,
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
        "observables": ["output", "rolling_k3"],
        "pca_dims": [2, 4],
        "clustering": {
            "method": "kmeans",
            "kmeans": {"n_clusters": 3},
            "dbscan": {"eps": 0.35, "min_samples": 4},
        },
        "recurrence": {"metric": "cosine", "epsilon": 0.5, "tau": 2},
        "dwell": {"space": "pca4"},
        "basin": {
            "target_region_late_fraction": 0.4,
            "target_step_fraction": 0.5,
            "perturbations": ["seed_only"],
        },
        "baseline_modes": ["no_feedback"],
        "batch_embeddings": False,
        "use_evals": False,
        "seed": 1,
        "parallel_trajectories": 1,
        "output_dir": str(tmp_path),
        "prompt_families": [
            {
                "name": "toy",
                "system_prompt": "Continue.",
                "initial_conditions": [
                    "alpha seed one",
                    "beta seed two",
                ],
            }
        ],
    }
    path = tmp_path / "cfg.yaml"
    path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    return path


@pytest.fixture
def fake_client(monkeypatch):
    class FakeClient:
        pass

    def make_fake_client():
        return FakeClient()

    monkeypatch.setattr(client_mod, "make_client", make_fake_client)
    # also patch main.make_client reference that was imported by name
    monkeypatch.setattr(cli, "make_client", make_fake_client)

    def fake_generate_step(client, context_text, config, system_prompt=None, **kwargs):
        # Deterministic varied output so embeddings differ step to step.
        h = (hash(context_text) & 0xFFFF) % 7
        words = ["calm", "bright", "hollow", "open", "slow", "edge", "fold"]
        out = " " + words[h] + " " + words[(h + 3) % 7]
        return GenerationResult(
            output_text=out,
            model="fake-gen",
            response_id="fake",
            latency_sec=0.0,
            retries=0,
            raw={"fake": True},
            logprobs=None,
        )

    monkeypatch.setattr(trajectory_mod, "generate_step", fake_generate_step)

    def fake_embed_texts(client, texts, config, **kwargs):
        rng = np.random.default_rng(0)
        vecs = []
        for t in texts:
            seed = (hash(t) & 0xFFFFFFFF) ^ 0x9E3779B1
            rngi = np.random.default_rng(seed)
            v = rngi.normal(size=8).astype(np.float32)
            v += rng.normal(scale=0.02, size=8).astype(np.float32)
            vecs.append(v)
        mat = np.array(vecs, dtype=np.float32)
        mat /= (np.linalg.norm(mat, axis=1, keepdims=True) + 1e-12)
        return mat

    monkeypatch.setattr(embedder_mod, "embed_texts", fake_embed_texts)
    monkeypatch.setattr(cli, "embed_texts", fake_embed_texts)


def test_end_to_end_all(tmp_path, fake_client):
    cfg_path = _write_tiny_config(tmp_path)
    rc = cli.main(["all", "--config", str(cfg_path), "--log-level", "WARNING"])
    assert rc == 0

    exp_dir = tmp_path / "exp_test"
    assert (exp_dir / "config.yaml").exists()
    assert (exp_dir / "raw" / "steps.jsonl").exists()
    assert (exp_dir / "metrics" / "recurrence.csv").exists()
    assert (exp_dir / "metrics" / "dwell.csv").exists()
    assert (exp_dir / "reports" / "report.md").exists()

    report = (exp_dir / "reports" / "report.md").read_text(encoding="utf-8")
    assert "Classification" in report
    assert "exp_test" in report
