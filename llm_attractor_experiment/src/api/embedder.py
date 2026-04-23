from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Iterable

import numpy as np
from openai import OpenAI

from src.config import Config
from src.utils.logging import get_logger

log = get_logger(__name__)


@dataclass
class EmbeddingBatch:
    vectors: np.ndarray  # shape (n, d), float32, L2-normalized
    model: str
    latency_sec: float
    retries: int


_RETRYABLE_HINTS = (
    "rate limit",
    "timeout",
    "temporar",
    "overload",
    "503",
    "502",
    "500",
    "connection",
)


def _is_retryable(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(h in msg for h in _RETRYABLE_HINTS)


def _chunks(seq: list[str], n: int) -> Iterable[list[str]]:
    for i in range(0, len(seq), n):
        yield seq[i : i + n]


def embed_texts(
    client: OpenAI,
    texts: list[str],
    config: Config,
    batch_size: int = 128,
    max_retries: int = 5,
    base_delay: float = 2.0,
    normalize: bool = True,
) -> np.ndarray:
    """Embed a list of strings; returns an (n, d) float32 array (L2-normalized)."""
    if not texts:
        return np.zeros((0, 0), dtype=np.float32)

    cleaned: list[str] = []
    for t in texts:
        if not t or not t.strip():
            # OpenAI rejects empty inputs; substitute a single space sentinel
            cleaned.append(" ")
        else:
            cleaned.append(t)

    all_vecs: list[np.ndarray] = []
    for batch in _chunks(cleaned, batch_size):
        vecs = _embed_batch(client, batch, config, max_retries, base_delay)
        all_vecs.append(vecs)
    mat = np.concatenate(all_vecs, axis=0).astype(np.float32, copy=False)
    if normalize:
        norms = np.linalg.norm(mat, axis=1, keepdims=True) + 1e-12
        mat = mat / norms
    return mat


def _embed_batch(
    client: OpenAI,
    batch: list[str],
    config: Config,
    max_retries: int,
    base_delay: float,
) -> np.ndarray:
    last_exc: Exception | None = None
    for attempt in range(max_retries + 1):
        t0 = time.monotonic()
        try:
            resp = client.embeddings.create(
                model=config.embedding_model,
                input=batch,
            )
            latency = time.monotonic() - t0
            log.debug(
                "embeddings.create n=%d model=%s latency=%.2fs",
                len(batch),
                config.embedding_model,
                latency,
            )
            return np.array([d.embedding for d in resp.data], dtype=np.float32)
        except Exception as exc:
            last_exc = exc
            if attempt >= max_retries or not _is_retryable(exc):
                log.error("embeddings.create failed (attempt %d): %s", attempt, exc)
                raise
            delay = base_delay * (2**attempt) + random.uniform(0, 0.5)
            log.warning(
                "embeddings.create retryable error (attempt %d, sleeping %.1fs): %s",
                attempt,
                delay,
                exc,
            )
            time.sleep(delay)
    raise RuntimeError(f"embed_batch exhausted retries: {last_exc}")
