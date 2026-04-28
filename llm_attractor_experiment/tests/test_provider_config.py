"""Cross-model provider abstraction: config parsing + dispatch."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml

from src.api.generator import generate_step
from src.config import Config, ProviderConfig, load_config


def _minimal_yaml(provider_block: dict | None = None, model: str = "gpt-4o-mini") -> dict:
    base = {
        "experiment_id": "exp_test_provider",
        "generation_model": model,
        "embedding_model": "text-embedding-3-small",
        "steps_per_run": 1,
        "runs_per_condition": 1,
        "initial_conditions_per_family": 1,
        "max_output_tokens": 16,
        "temperature": 0.8,
        "top_p": 1.0,
        "prompt_families": [
            {"name": "f1", "system_prompt": "test", "initial_conditions": ["seed"]}
        ],
    }
    if provider_block is not None:
        base["generation_provider"] = provider_block
    return base


def test_config_defaults_to_openai_responses_when_block_absent(tmp_path):
    """Every existing exp_pub_* config in the repo lacks a
    `generation_provider` block — we must default it to the OpenAI
    native Responses API for backward compat."""
    p = tmp_path / "cfg.yaml"
    p.write_text(yaml.safe_dump(_minimal_yaml()))
    cfg = load_config(p)
    assert cfg.generation_provider.name == "openai"
    assert cfg.generation_provider.api == "responses"
    assert cfg.generation_provider.api_key_env == "OPENAI_API_KEY"
    assert cfg.generation_provider.base_url is None


def test_config_parses_minimax_block(tmp_path):
    p = tmp_path / "cfg.yaml"
    p.write_text(yaml.safe_dump(_minimal_yaml(
        provider_block={
            "name": "minimax",
            "base_url": "https://api.minimaxi.chat/v1",
            "api_key_env": "MINIMAX_API_KEY",
            "api": "chat_completions",
        },
        model="MiniMax-Text-01",
    )))
    cfg = load_config(p)
    assert cfg.generation_provider.name == "minimax"
    assert cfg.generation_provider.base_url == "https://api.minimaxi.chat/v1"
    assert cfg.generation_provider.api_key_env == "MINIMAX_API_KEY"
    assert cfg.generation_provider.api == "chat_completions"
    assert cfg.generation_model == "MiniMax-Text-01"


def test_config_rejects_unknown_api(tmp_path):
    p = tmp_path / "cfg.yaml"
    p.write_text(yaml.safe_dump(_minimal_yaml(
        provider_block={"name": "openai", "api": "bogus_api"},
    )))
    with pytest.raises(ValueError, match="generation_provider.api"):
        load_config(p)


def _cfg_with_provider(api: str) -> Config:
    return Config(
        experiment_id="t", generation_model="m", embedding_model="e",
        generation_provider=ProviderConfig(api=api),
        steps_per_run=1, runs_per_condition=1,
        initial_conditions_per_family=1, max_output_tokens=16,
        temperature=0.5, top_p=1.0, include_logprobs=False,
        clip_rule="tail_chars", max_context_chars=12000,
        rolling_window_k=3, context_tail_chars=4000, context_full_chars=8000,
        observables=[], pca_dims=[2, 10],
        clustering=None, recurrence=None, dwell=None, basin=None,  # type: ignore
        tsne=None, basin_entry=None, late_recurrence=None,         # type: ignore
        exit_return=None, bootstrap=None,                          # type: ignore
        baseline_modes=[], batch_embeddings=False, use_evals=False,
        seed=42, parallel_trajectories=1, output_dir="data",
        prompt_families=[],
    )


def test_generate_step_dispatches_to_responses_api():
    cfg = _cfg_with_provider("responses")
    fake = MagicMock()
    fake.responses.create.return_value = MagicMock(
        output_text="hello", model="m", id="r1", model_dump=lambda: {}
    )
    out = generate_step(fake, "context", cfg)
    assert out.output_text == "hello"
    fake.responses.create.assert_called_once()
    fake.chat.completions.create.assert_not_called()


def test_generate_step_dispatches_to_chat_completions_api():
    cfg = _cfg_with_provider("chat_completions")
    msg = MagicMock(); msg.content = "world"
    choice = MagicMock(); choice.message = msg; choice.logprobs = None
    fake = MagicMock()
    fake.chat.completions.create.return_value = MagicMock(
        choices=[choice], model="m", id="c1", model_dump=lambda: {}
    )
    out = generate_step(fake, "context", cfg)
    assert out.output_text == "world"
    fake.chat.completions.create.assert_called_once()
    fake.responses.create.assert_not_called()
