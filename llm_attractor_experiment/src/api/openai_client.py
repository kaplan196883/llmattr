"""SDK client construction for both generation and embedding paths.

Generation can target any OpenAI-compatible vendor (OpenAI, MiniMax,
DeepSeek, etc.); embeddings always stay on OpenAI for a consistent
geometric space across cross-model runs. See `src/config.py
ProviderConfig`.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from src.config import ProviderConfig


def _load_env() -> None:
    here = Path(__file__).resolve()
    for parent in [Path.cwd(), *here.parents]:
        candidate = parent / ".env"
        if candidate.exists():
            load_dotenv(candidate, override=False)
            break


def make_generation_client(provider: ProviderConfig | None = None) -> OpenAI:
    """SDK client for the generation model. Honors `base_url` and
    `api_key_env` from the provider config so MiniMax / OpenAI-compatible
    vendors work via the same `openai` Python SDK."""
    _load_env()
    provider = provider or ProviderConfig()
    key = os.environ.get(provider.api_key_env)
    if not key:
        raise RuntimeError(
            f"{provider.api_key_env} not set. Add it to .env in the project "
            f"root or parent (provider={provider.name!r})."
        )
    kwargs: dict = {"api_key": key}
    if provider.base_url:
        kwargs["base_url"] = provider.base_url
    return OpenAI(**kwargs)


def make_embedding_client() -> OpenAI:
    """SDK client for the embedding model. Always OpenAI native — the
    embedding space is held fixed across cross-model runs so PCA-10 /
    cluster / V* comparisons remain meaningful."""
    _load_env()
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError(
            "OPENAI_API_KEY not set. Embeddings always go through OpenAI for "
            "geometric-space consistency across cross-model runs."
        )
    return OpenAI(api_key=key)


def make_client() -> OpenAI:
    """Backwards-compat alias used by older entry points. Returns the
    same client as `make_embedding_client()` (i.e., OpenAI native).
    New code should call `make_generation_client(cfg.generation_provider)`
    or `make_embedding_client()` explicitly."""
    return make_embedding_client()
